# from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

# model = ChatOpenAI(model="gpt-4o-mini")
model = ChatOllama(model="deepseek-r1:14b")

messages = [
  SystemMessage(content="너는 사용자를 도와주는 상담사야. 사용자의 질문에 한국어로 답변해야 한다.")
]

while True:
  user_input = input("사용자: ")
  
  if user_input == "exit":
    break
  
  messages.append(HumanMessage(user_input))
  response = model.stream(messages)
  ai_message = None

  for chunk in response:
    # 스트리밍된 토큰을 바로 콘솔에 출력
    if chunk.content:
      print(chunk.content, end="", flush=True)

    # 전체 AIMessageChunk를 누적해서 마지막에 history에 넣기
    if ai_message is None:
      ai_message = chunk
    else:
      ai_message += chunk

  print()  # 한 턴 끝난 후 줄바꿈

  if ai_message is not None:
    messages.append(AIMessage(content=ai_message.content))