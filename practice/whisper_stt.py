import unicodedata
from pathlib import Path

import torch
import pandas as pd
import librosa
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from pyannote.audio import Pipeline
from dotenv import load_dotenv
import os


def _abs_from_file(*parts: str) -> Path:
    """이 파일(__file__) 기준으로 절대경로 생성 + macOS 한글 정규화(NFC)."""
    base = Path(__file__).resolve().parent
    p = (base.joinpath(*parts)).resolve()
    return Path(unicodedata.normalize("NFC", str(p)))


def whisper_stt(
    audio_file_path: str,
    output_file_path: str = "./output.csv",
):
    # ----- 디바이스/정밀도 -----
    if torch.cuda.is_available():
        device_for_model = "cuda:0"
        torch_dtype = torch.float16
        pipeline_device = 0          # transformers pipeline용
    else:
        device_for_model = "cpu"
        torch_dtype = torch.float32
        pipeline_device = -1

    model_id = "openai/whisper-large-v3-turbo"

    # ----- 모델/프로세서 로드 -----
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
    ).to(device_for_model)

    processor = AutoProcessor.from_pretrained(model_id)

    asr = pipeline(
        task="automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        return_timestamps=True,
        chunk_length_s=15,
        stride_length_s=3,
        device=pipeline_device,  # CUDA면 0, 그 외 -1
    )

    # ----- 경로 정리 -----
    audio_path = _abs_from_file(audio_file_path)
    out_path = _abs_from_file(output_file_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not audio_path.exists():
        raise FileNotFoundError(f"Not found: {audio_path}")

    # ----- ✅ torchcodec 우회: librosa로 mp3 → numpy 배열 -----
    # sr은 Whisper 권장 16kHz, mono로 리샘플/모노화
    audio, sr = librosa.load(str(audio_path), sr=16000, mono=True)

    # numpy 배열 입력 형식으로 전달 → 파일 디코딩 단계를 우회
    result = asr({"array": audio, "sampling_rate": sr})

    df = whisper_to_dataframe(result)
    df.to_csv(out_path, index=False, sep=" ", encoding="utf-8")

    return result, df


def whisper_to_dataframe(result):
    rows = []
    for chunk in result.get("chunks", []):
        start, end = chunk.get("timestamp", [None, None])
        text = (chunk.get("text") or "").strip()
        rows.append([start, end, text])
    return pd.DataFrame(rows, columns=["start", "end", "text"])

def speaker_diarization(
    audio_file_path: str,
    output_rttm_file_path: str,
    output_csv_file_path: str
):
    audio_file_path = _abs_from_file(audio_file_path)
    output_rttm_file_path = _abs_from_file(output_rttm_file_path)
    output_csv_file_path = _abs_from_file(output_csv_file_path)
    
    load_dotenv()

    api_key = os.getenv("HUGGING_API_KEY")

    pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=api_key
    )

    if torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))
        print("cuda is available")
    else:
        pipeline.to(torch.device("cpu"))
        print("cuda is not available")
        
    diarization_pipeline = pipeline(audio_file_path)
    
    with open(output_rttm_file_path, "w", encoding="utf-8") as rttm:
        diarization_pipeline.write_rttm(rttm)
        
    df_rttm = pd.read_csv(
        output_rttm_file_path,
        sep= ' ',
        header=None,
        names=['type', 'file', 'chnl', 'start', 'duration', 'C1', 'C2', 'speaker_id', 'C3', 'C4']
    )
    
    df_rttm["end"] = df_rttm["start"] + df_rttm["duration"]
    df_rttm["number"] = None
    df_rttm.at[0, "number"] = 0
    
    for i in range(1, len(df_rttm)):
        if df_rttm.at[i, 'speaker_id'] != df_rttm.at[i-1, 'speaker_id']:
            df_rttm.at[i, 'number'] = df_rttm.at[i-1, 'number'] + 1
        else:
            df_rttm.at[i, 'number'] = df_rttm.at[i-1, 'number']
            
    df_rttm_grouped = df_rttm.groupby("number").agg(
        start=pd.NamedAgg(column='start', aggfunc='min'),
        end=pd.NamedAgg(column='end', aggfunc='max'),
        speaker_id=pd.NamedAgg(column='speaker_id', aggfunc='first')
    )

    df_rttm_grouped["duration"] = df_rttm_grouped["end"] - df_rttm_grouped["start"]
    
    df_rttm_grouped.to_csv(
        output_csv_file_path,
        index=False,
        encoding="utf-8"
    )
    
    return df_rttm_grouped

def stt_to_rttm (
    audio_file_path: str,
    stt_output_file_path: str,
    rttm_file_path: str,
    rttm_csv_file_path: str,
    final_output_csv_file_path: str
):
    
    audio_file_path = _abs_from_file(audio_file_path)
    stt_output_file_path = _abs_from_file(stt_output_file_path)
    rttm_file_path = _abs_from_file(rttm_file_path)
    rttm_csv_file_path = _abs_from_file(rttm_csv_file_path)
    final_output_csv_file_path = _abs_from_file(final_output_csv_file_path)
    
    result, df_stt = whisper_stt(
        audio_file_path,
        stt_output_file_path
    )
    
    df_rttm = speaker_diarization(
        audio_file_path,
        rttm_file_path,
        rttm_csv_file_path
    )
    
    df_rttm["text"] = ""
    
    for i_stt, row_stt in df_stt.iterrows(): 
        overlap_dict = {}
        for i_rttm, row_rttm in df_rttm.iterrows():
            overlap = max(0, min(row_stt["end"], row_rttm["end"]) - max(row_stt["start"], row_rttm["start"]))
            overlap_dict[i_rttm] = overlap
            
        max_overlap = max(overlap_dict.values())
        max_overlap_idx = max(overlap_dict, key=overlap_dict.get)
        
        if (max_overlap > 0):
            df_rttm.at[max_overlap_idx, "text"] += row_stt["text"] + "\n"
    
    df_rttm.to_csv(
        final_output_csv_file_path,
        index=False,
        sep="|",
        encoding="utf-8"
    )
    
    return df_rttm

if __name__ == "__main__":
    audio_file_path = "./audio/guitar.mp3"
    stt_output_file_path = "./audio/guitar.csv"
    rttm_file_path = "./audio/guitar.rttm"
    rttm_csv_file = "./audio/guitar_rttm.csv"
    final_csv_file_path = "./audio/guitar_final.csv"
    # 예시: 현재 파일이 practice/whisper_stt.py 이고 오디오가 practice/audio/ 아래에 있을 때
    # result, df = whisper_stt("./audio/guitar.mp3", "./audio/guitar.csv")
    # print(df)
    
    # df_rttm = speaker_diarization(
    #     "./audio/guitar.mp3",
    #     "./audio/guitar.rttm",
    #     "./audio/guitar_rttm.csv"
    # )
    # print(df_rttm)
    
    df_rttm = stt_to_rttm(
        audio_file_path,
        stt_output_file_path,
        rttm_file_path,
        rttm_csv_file,
        final_csv_file_path
    )
    