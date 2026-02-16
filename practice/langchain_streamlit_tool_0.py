import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

load_dotenv()

st.title("AI Chatbot")

model = ChatOpenAI(model="gpt-4o-mini")


def get_ai_response(messages):
  response = model.stream(messages)
  
  for chunk in response:
    yield chunk

if "messages" not in st.session_state:
  st.session_state["messages"] = [
    SystemMessage(content="너는 사용자를 돕기 위해 최선을 다하는 인공지능 봇이다."),
    AIMessage(content="안녕하세요! 무엇을 도와드릴까요?"),
  ]
  
  
for msg in st.session_state.messages:
  if msg:
    if isinstance(msg, SystemMessage):
      st.chat_message("system").write(msg.content)
    elif isinstance(msg, AIMessage):
      st.chat_message("assistant").write(msg.content)
    elif isinstance(msg, HumanMessage):
      st.chat_message("user").write(msg.content)
      
if prompt := st.chat_input():
  st.session_state.messages.append(HumanMessage(content=prompt))
  st.chat_message("user").write(prompt)
  
  response = get_ai_response(st.session_state.messages)
  
  result = st.chat_message("assistant").write_stream(response)
  st.session_state["messages"].append(AIMessage(content=result))