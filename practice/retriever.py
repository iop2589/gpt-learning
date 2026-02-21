from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()

embedding = OpenAIEmbeddings(model="text-embedding-3-large")

from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o")

from langchain_chroma import Chroma
persist_directory = "/Users/parksc/Documents/pythonworkspace/gptproject01/chroma_store1"

vectorstore = Chroma(
  persist_directory=persist_directory,
  embedding_function=embedding
)

retriever = vectorstore.as_retriever(k=3)

from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

question_answering_prompt = ChatPromptTemplate.from_messages(
  [
    (
      "system", "사용자의 질문에 대해 아래 context에 기반하여 답변하라.:\n\n{context}",
    ),
    MessagesPlaceholder(variable_name="messages"),
  ]
)

document_chain = create_stuff_documents_chain(
  llm,
  question_answering_prompt
) | StrOutputParser()

query_augmentation_prompt = ChatPromptTemplate.from_messages(
  [
    MessagesPlaceholder(variable_name="messages"),
    (
      "system", "기존의 대화내용을 활용하여 사용자가 질문한 의도를 파악해서 한 문장의 명료한 질문으로 변환하라. 대명사나 이, 저, 그와 같은 표현을 명확한 명사로 표현하라. :\n\n{query}",
    ),
  ]
)

query_augmentation_chain = query_augmentation_prompt | llm | StrOutputParser()
