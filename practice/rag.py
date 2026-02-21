import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
import retriever

load_dotenv()

st.title("AI Chatbot")

model = ChatOpenAI(model="gpt-4o-mini")


def get_ai_response(messages, docs):
  response = retriever.document_chain.stream(
    {
      "messages": messages,
      "context": docs
    }
  ) # model.stream(messages)
  
  for chunk in response:
    yield chunk

if "messages" not in st.session_state:
  st.session_state["messages"] = [
    SystemMessage(content="너는 문서에 기반해 답변하는 도시 정책 전문가야."),
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
  
  augmented_query = retriever.query_augmentation_chain.invoke(
    {
      "messages": st.session_state["messages"],
      "query": prompt
    }
  )
  
  print("augmented_query: ", augmented_query)
  
  print("관련문서 검색")
  docs = retriever.retriever.invoke(f"{prompt}\n{augmented_query}")
  
  for doc in docs:
    print('--------------------------------')
    print(doc)
    
    with st.expander(f"**문서:** {doc.metadata.get('source', 'Unknown')}"):
      st.write(f"**page:** {doc.metadata.get('page', 'Unknown')}")
      st.write(doc.page_content)
  
  with st.spinner(f"AI가 답변을 준비중 입니다...'{augmented_query}'"):
  
    response = get_ai_response(st.session_state.messages, docs) 
  
    result = st.chat_message("assistant").write_stream(response)
    
  st.session_state["messages"].append(AIMessage(content=result))