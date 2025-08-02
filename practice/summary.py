from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def summarize_text(file_path: str):
  client = OpenAI(api_key=api_key)
  
  with open(file_path, 'r', encoding='utf-8') as f:
    txt = f.read()
    
  system_prompt = f"""
  너는 다음 글을 읽고 요약하는 봇이야. 아래 글을 읽고, 저자가 우리에게 전달하려고 하는 점을 파악하고 주요 내용을 요역해줘
  작성해야하는 포맷을 다음과 같아
  
  - 제목
  - 전달 주요 내용
  - 저자 소개
  ===== 이하 텍스트 =====
  
  {txt}
  """
  
  print (system_prompt)
  print("--------------------------------")
  
  response = client.chat.completions.create(
    model="gpt-4o",
    temperature=0.1,
    messages=[
      {"role": "system", "content": system_prompt},
    ],
  )
  
  return response.choices[0].message.content

if __name__ == "__main__":
  file_path = "practice/output/text.txt"
  summary = summarize_text(file_path)
  print(summary)
  
  with open("practice/output/summary.txt", "w", encoding="utf-8") as f:
    f.write(summary)