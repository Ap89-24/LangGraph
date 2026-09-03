from langgraph.graph import StateGraph , START , END
from langchain_mistralai import ChatMistralAI
from typing import TypedDict , Literal , Annotated
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage , HumanMessage
from pydantic import BaseModel , Field
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
load_dotenv()



class chatState(TypedDict):
    
    messages: Annotated[list[BaseMessage], add_messages]
    
    


llm = ChatMistralAI()

def chat_node(state: chatState):
    
    messages = state['messages']
    
    response = llm.invoke(messages)
    
    return {'messages': [response]}



checkpointer = MemorySaver()

graph = StateGraph(chatState)

graph.add_node("chat_node", chat_node)

graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)




# thread_id = '1'

# while True:
    
#     user_message = input('Type here: ')
#     print('User: ' , user_message)
#     if(user_message.strip().lower() in ['exit','quit','bye']):
#         break
#     config = {'configurable': {'thread_id': thread_id}}
#     response = chatbot.invoke({'messages': HumanMessage(content=user_message)}, config=config)
#     print('AI: ' ,response['messages'][-1].content)    