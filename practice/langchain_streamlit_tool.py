import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from langchain_core.tools import tool
from datetime import datetime
import pytz

load_dotenv()
model = ChatOpenAI(model="gpt-4o-mini")

@tool
def get_current_time(timezone: str, location: str) -> str:
  """현재 시각을 반환하는 함수"""
  try:
    tz = pytz.timezone(timezone)
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    location_and_local_time = f"{timezone} ({location})의 현재 시각 {now}"
    print(location_and_local_time)
    return location_and_local_time
  except pytz.UnknownTimeZoneError:
    return f"Unknown timezone: {timezone}"
  
tools = [get_current_time]
tool_dict = {"get_current_time": get_current_time}

llm_with_tools = model.bind_tools(tools)
  
st.title("AI Chatbot")

def get_ai_response(messages):
  response = llm_with_tools.stream(messages)
  
  gathered = None
  
  for chunk in response:
    yield chunk
    
    if gathered is None:
      gathered = chunk
    else:
      gathered += chunk
  
  # gathered를 session_state에 저장하여 write_stream 호출 후 사용
  if gathered:
    st.session_state["last_gathered"] = gathered

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
    elif isinstance(msg, ToolMessage):
      st.chat_message("tool").write(msg.content)
      
if prompt := st.chat_input():
  st.session_state.messages.append(HumanMessage(content=prompt))
  st.chat_message("user").write(prompt)
  
  # gathered 초기화
  if "last_gathered" in st.session_state:
    del st.session_state["last_gathered"]
  
  response = get_ai_response(st.session_state.messages)
  
  # write_stream이 모든 chunk를 소비
  st.chat_message("assistant").write_stream(response)
  
  # write_stream 완료 후 gathered 처리
  if "last_gathered" in st.session_state:
    gathered = st.session_state["last_gathered"]
    # AIMessage를 메시지 히스토리에 추가
    st.session_state.messages.append(gathered)
    
    # tool_calls가 있으면 tool 실행
    if gathered.tool_calls:
      for tool_call in gathered.tool_calls:
        selected_tool = tool_dict[tool_call["name"]]
        tool_result = selected_tool.invoke(tool_call["args"])
        tool_msg = ToolMessage(
          content=tool_result,
          tool_call_id=tool_call["id"]
        )
        print(tool_msg, type(tool_msg))
        st.session_state.messages.append(tool_msg)
        
      # Tool 실행 후 다시 AI 응답 생성
      next_response = get_ai_response(st.session_state.messages)
      st.chat_message("assistant").write_stream(next_response)
      
      # 재귀 호출로 인한 gathered도 처리
      if "last_gathered" in st.session_state:
        next_gathered = st.session_state["last_gathered"]
        if next_gathered and not next_gathered.tool_calls:
          st.session_state.messages.append(next_gathered)