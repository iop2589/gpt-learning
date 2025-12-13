from openai import OpenAI
import os
from dotenv import load_dotenv
from gpt_functions import get_current_time, tools

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def get_ai_response(messages, tools=None):
  response = client.chat.completions.create(
    model="gpt-4o",
    temperature=0.9,
    messages=messages,
    tools=tools,
  )
  
  return response

messages = [
    {"role": "system", "content": "너는 사용자를 도와주는 상담사야."}
] # 시스템 설정 메세지

while True:
  user_input = input("사용자 : ")
  
  if (user_input == "exit"):
    break
  
  messages.append({"role": "user", "content": user_input})
  ai_response = get_ai_response(messages, tools)
  ai_message = ai_response.choices[0].message
  print(ai_message)
  
  tool_calls = ai_message.tool_calls
  
  if tool_calls:
    tool_name = tool_calls[0].function.name
    tool_call_id = tool_calls[0].id
    
    if tool_name == "get_current_time":
      messages.append(
        {
          "role": "function",
          "tool_call_id": tool_call_id,
          "name": tool_name,
          "content": get_current_time(),
        }
      )
      
    ai_response = get_ai_response(messages, tools)
    ai_message = ai_response.choices[0].message
    
  messages.append(ai_message)
  
  print("AI: ", ai_message.content)