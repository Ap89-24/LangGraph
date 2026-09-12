from langgraph.graph import StateGraph , START , END
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict , Literal , Annotated
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage , HumanMessage
from pydantic import BaseModel , Field
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
import sqlite3
load_dotenv()



class chatState(TypedDict):
    
    messages: Annotated[list[BaseMessage], add_messages]
    
    


llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")

def chat_node(state: chatState):
    
    messages = state['messages']
    
    response = llm.invoke(messages)
    
    return {'messages': [response]}


connection = sqlite3.connect(database='chatbot.db' , check_same_thread=False)

checkpointer = SqliteSaver(conn=connection)

graph = StateGraph(chatState)

graph.add_node("chat_node", chat_node)

graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)


def retrieve_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]['thread_id'])
        
    return list(all_threads)   