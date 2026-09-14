from langgraph.graph import StateGraph , START , END
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict , Literal , Annotated
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage , HumanMessage
from pydantic import BaseModel , Field
from langgraph.prebuilt import ToolNode , tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
import sqlite3
import requests
import os
load_dotenv()


llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))

#Tools

search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations are: add,  sub, mul, div 
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}                


@tool
def get_stock(symbol: str) -> dict:
    """
    Fetch the latest stock price for a given symbol (e.g -> 'AAPL' , 'TSLA')
    using alpha vantage with api key in hte url.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=YAOR3VOY60ZOFZJP"
    r = requests.get(url)
    return r.json()

tools = [get_stock, calculator, search_tool]

llm_with_tools = llm.bind_tools(tools)

class chatState(TypedDict):
    
    messages: Annotated[list[BaseMessage], add_messages]
    


def chat_node(state: chatState):
    
    """ LLM node that may answer or request a tool call """
    messages = state['messages']
    
    response = llm_with_tools.invoke(messages)
    
    return {'messages': [response]}

tool_node = ToolNode(tools)   #Execute tool calls....


connection = sqlite3.connect(database='chatbot.db' , check_same_thread=False)

checkpointer = SqliteSaver(conn=connection)

graph = StateGraph(chatState)

graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
# If the LLM asked for a tool, go to ToolNode; else finish...
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)


def retrieve_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]['thread_id'])
        
    return list(all_threads)   