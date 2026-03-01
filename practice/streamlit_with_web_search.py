import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from langchain_core.tools import tool
from datetime import datetime
import pytz

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

from youtube_search import YoutubeSearch
from langchain_community.document_loaders import YoutubeLoader
from typing import List
import json

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
  
@tool
def get_web_search(query: str, search_period: str) -> str:
  """
  웹 검색을 수행하는 함수
  Args:
    query (str): 검색어
    search_period (str): 검색 기간 (e.g., "w" for past week, "m" for past month, "y" for past year)
  Returns:
    str: 검색 결과
  """
  wrapper = DuckDuckGoSearchAPIWrapper(region="kr-kr", time=search_period)
  
  print('------------------ Web Search ------------------')
  print(f'query: {query}')
  print(f'search_period: {search_period}')
  
  search = DuckDuckGoSearchResults(api_wrapper=wrapper, results_separator="\n")
  result = search.invoke({"query": query})
  return result

@tool
def get_youtube_search(query: str) -> List:
  """
  Youtube 검색을 수행한뒤, 영상들의 내용을 반환하는 함수
  Args:
    query (str): 검색어
  Returns:
    List: 검색 결과 (각 영상의 title, video_url, content 포함)
  """
  print('------------------ Youtube Search ------------------')
  print(f'query: {query}')
  print('----------------------------------------------------')
  
  videos = YoutubeSearch(query, max_results=5).to_dict()
  videos = [v for v in videos if len(v.get('duration', '').split(':')) <= 5]
  for v in videos:
    v['video_url'] = 'https://www.youtube.com' + v['url_suffix']
    loader = YoutubeLoader.from_youtube_url(v['video_url'], language=['ko', 'en'])
    docs = loader.load()
    v['content'] = "\n\n".join([doc.page_content for doc in docs])
  return videos
  
tools = [get_current_time, get_web_search, get_youtube_search]
tool_dict = {"get_current_time": get_current_time, "get_web_search": get_web_search, "get_youtube_search": get_youtube_search}

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
        # ToolMessage content는 문자열이어야 함 (OpenAI API 요구사항)
        content = json.dumps(tool_result, ensure_ascii=False) if not isinstance(tool_result, str) else tool_result
        tool_msg = ToolMessage(
          content=content,
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