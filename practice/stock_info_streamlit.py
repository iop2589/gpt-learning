from openai import OpenAI
import os
from dotenv import load_dotenv
from gpt_functions import get_current_time, tools, get_yf_stock_info, get_yf_stock_history, get_yf_stock_recommendations
import json
import streamlit as st
from collections import defaultdict

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def tool_list_to_tool_obj(tools):
  tool_calls_dict = defaultdict(lambda:{"id": None, "function": {"arguments": "", "name": None}, "type": None})
  
  for tool_call in tools:
    if tool_call.id is not None:
      tool_calls_dict[tool_call.index]["id"] = tool_call.id

    if tool_call.function.name is not None:
      tool_calls_dict[tool_call.index]["function"]["name"] = tool_call.function.name
      
    tool_calls_dict[tool_call.index]["function"]["arguments"] += tool_call.function.arguments
    
    if tool_call.type is not None:
      tool_calls_dict[tool_call.index]["type"] = tool_call.type
      
  tool_calls_list = list(tool_calls_dict.values())
      
  return {"tool_calls": tool_calls_list}
  

def get_ai_response(messages, tools=None, stream=True):
  response = client.chat.completions.create(
    model="gpt-4o",
    stream=stream,
    temperature=0.9,
    messages=messages,
    tools=tools,
  )
  
  if stream:
    for chunk in response:
      yield chunk
  else:
    return response

st.title("ChatBot")

if "messages" not in st.session_state:
  st.session_state["messages"] = [{"role": "system", "content": "너는 사용자를 도와주는 상담사야."}]
  
for msg in st.session_state.messages:
  st.chat_message(msg["role"]).write(msg["content"])

  
if user_input := st.chat_input():
  st.session_state.messages.append({"role": "user", "content": user_input})
  st.chat_message("user").write(user_input)
  
ai_response = get_ai_response(st.session_state.messages, tools)

content = ''
tool_calls = None
tool_calls_chunk = []

with st.chat_message("assistant").empty():
  for chunk in ai_response:
    content_chunk = chunk.choices[0].delta.content
    if content_chunk:
      print(content_chunk)
      content += content_chunk
      st.markdown(content)
    
    if chunk.choices[0].delta.tool_calls:
      tool_calls_chunk += chunk.choices[0].delta.tool_calls
    
  tool_obj = tool_list_to_tool_obj(tool_calls_chunk)
  tool_calls = tool_obj["tool_calls"]
  
  if len(tool_calls) > 0:
    print(tool_calls)
    tool_call_msg = [tool_call["function"] for  tool_call in tool_calls]
    st.write(tool_call_msg)
  
    
print("\n--------------------------------")

print(content)

# print('\n-------------------------------- tool_calls_chunk --------------------------------')
# for tool_call_chunk in tool_calls_chunk:
#   print(tool_call_chunk)

print(tool_calls)

# ai_message = ai_response.choices[0].message

# print(ai_message)

# tool_calls = ai_message.tool_calls

if tool_calls:
  
  for tool_call in tool_calls:
    tool_name = tool_call["function"]["name"]
    tool_call_id = tool_call["id"]
    arguments =json.loads(tool_call["function"]["arguments"])
    
    timezone = arguments.get("timezone", "Asia/Seoul")
    
    if tool_name == "get_current_time":
      func_result = get_current_time(timezone=timezone)
    elif tool_name == "get_yf_stock_info":
      func_result = get_yf_stock_info(ticker=arguments.get("ticker", "MSFT"))
    elif tool_name == "get_yf_stock_history":
      func_result = get_yf_stock_history(ticker=arguments.get("ticker", "MSFT"), period=arguments.get("period", "5d"))
    elif tool_name == "get_yf_stock_recommendations":
      func_result = get_yf_stock_recommendations(ticker=arguments.get("ticker", "MSFT"))
      
    st.session_state.messages.append(
        {
          "role": "function",
          "tool_call_id": tool_call_id,
          "name": tool_name,
          "content": func_result,
        }
      )
      
      
  st.session_state.messages.append({
    "role": "system",
    "content": "이제 주어진 결과를 바탕으로 답변할 차례야",
  })
    
  ai_response = get_ai_response(st.session_state.messages, tools)
  # ai_message = ai_response.choices[0].message
  
  content = ''
  with st.chat_message("assistant").empty():
    for chunk in ai_response:
      content_chunk = chunk.choices[0].delta.content
      if content_chunk:
        print(content_chunk)
        content += content_chunk
        st.markdown(content)
  
st.session_state.messages.append(
  {
    "role": "assistant",
    "content": content,
  }
)

print("AI: ", content)

# st.chat_message("assistant").write(ai_message.content)