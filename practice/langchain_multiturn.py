from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")

messages = [
  SystemMessage(content="너는 사용자를 도와주는 상담사야.")
]

while True:
  user_input = input("사용자: ")
  
  if user_input == "exit":
    break
  
  messages.append(HumanMessage(user_input))
  response = model.invoke(messages)
  messages.append(response)
  
  print("AI: " + response.content)
