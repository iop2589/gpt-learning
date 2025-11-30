from glob import glob
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
import base64
import json

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 스크립트 파일의 디렉토리 경로를 기준으로 설정 (pathlib 사용)
SCRIPT_DIR = Path(__file__).parent

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode("utf-8")
  
  
  
def image_quiz(image_path, n_trial=0, max_trial=3 ):
  if n_trial >= max_trial:
    return f"Error: Failed to generate quiz after {max_trial} trials."
  
  image_base64 = encode_image(image_path)
  
  quiz_prompt = """
    제공한 이미지를 바탕으로, 다음과 같은 양식으로 퀴즈를 만들어 주세요. 
    정답은 (1) ~ (4) 중 하나만 해당하도록 출제하세요.
    토익 리스닝 문제 스타일로 문제를 제출해주세요.
    아래는 예시 입니다.
    Q: 다음 이미지에 대한 설명 중 옳지 않은 것은 무엇인가요?
    - (1) 베이커리에서 사람들이 빵을 사는 모습이 담겨 있습니다.
    - (2) 맨 앞에 서 있는 사람은 빨간색 셔츠를 입었습니다.
    - (3) 기차를 타기 위해 줄을 서 있는 사람들이 있습니다.
    - (4) 점원은 노란색 티셔츠를 입었습니다. 
    
    Listening: Which of the following descriptions of the image is incorrect?
    - (1) The image shows people buying bread at a bakery.
    - (2) The person in the front is wearing a red shirt.
    - (3) People are lined up to board a train.
    - (4) The cashier is wearing a yellow shirt.
    
    정답 : (4) 점원은 노란색 티셔츠가 아닌 파란색 티셔츠를 입었습니다.
    (주의: 정답은 (1) ~ (4) 중 하나만 해당하도록 출제하세요.)
  """
  
  messages = [
    {"role": "system", "content": quiz_prompt},
    {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}]},
  ]
  
  try:
    response = client.chat.completions.create(
      model="gpt-5-mini",
      messages=messages,
    )
  except Exception as e:
    return f"Error: {e}"
    n_trial += 1
    return image_quiz(image_path, n_trial, max_trial)
  
  content = response.choices[0].message.content
  
  if "Listening:" in content:
    return content, True
  else:
    n_trial += 1
    return image_quiz(image_path, n_trial, max_trial)

# 스크립트 파일 위치 기준으로 data 디렉토리 경로 설정
# image_path = SCRIPT_DIR / "data" / "art.jpeg"
# q = image_quiz(image_path)
# print(q)


txt = ""
eng_dict = []
no = 1
for g in glob(str(SCRIPT_DIR / "data" / "*.jpeg")):
  q, success = image_quiz(g)
  if not success:
    print(f"Error: Failed to generate quiz for {g}")
    continue
  
  divider = f"## 문제 : {no}\n\n"
  print(divider)
  
  txt += divider 
  filename = os.path.basename(g)
  txt += f"![image]({filename})\n\n"
  
  print(q)
  
  txt += q + "\n\n--------------------------------\n\n"
  
  with open(SCRIPT_DIR / "data" / "image_quiz.md", "w", encoding="utf-8") as f:
    f.write(txt)  
  
  eng = q.split("Listening:")[1].split("정답 :")[0].strip()
  img = filename
  eng_dict.append({
    "no": no,
    "eng": eng,
    "img": filename
  })
  
  with open(SCRIPT_DIR / "data" / "image_quiz.json", "w", encoding="utf-8") as f:
    json.dump(eng_dict, f, ensure_ascii=False, indent=4)
  
  no += 1
  print(f"Success: Generated quiz for {g}")
