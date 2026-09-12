import streamlit as st 
from chatbot_backend import chatbot , retrieve_threads
from langchain_core.messages import HumanMessage
import time
import uuid


def uuid_generator():
    id = uuid.uuid4()
    return str(id)
  
def reset_chat():
    thread_id = uuid_generator()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id']) 
    st.session_state['message_history'] = []    
    
def add_thread(thread_id):
    if thread_id not in st.session_state['chat_thread']:
        st.session_state['chat_thread'].append(thread_id)    

def load_conversation(thread_id):
     state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
     return state.values.get('messages', [])    


def extract_text(content):
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        return str(content)

   
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []   

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = uuid_generator()    

if 'chat_thread' not in st.session_state:
    st.session_state['chat_thread'] = retrieve_threads()    

add_thread(st.session_state['thread_id'])    

st.sidebar.title("LangGraph ChatBot")
if st.sidebar.button("New Chat"):
    reset_chat()
st.sidebar.header("Chat History") 

for thread_id in st.session_state['chat_thread'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)
        
        temp_message = []
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                temp_message.append({'role': 'user', 'content': extract_text(msg.content)})
            else:
                temp_message.append({'role': 'assistant', 'content': extract_text(msg.content)})
                
        st.session_state['message_history'] = temp_message        
           


def stream_with_delay(chunks, delay=0.03):
    for chunk in chunks:
        # Handle both plain-string and block-list content
        if isinstance(chunk, str):
            text = chunk
        elif isinstance(chunk, list):
            text = "".join(
                block.get("text", "")
                for block in chunk
                if isinstance(block, dict) and block.get("type") == "text"
            )
        else:
            text = str(chunk)

        if text:
            time.sleep(delay)
            yield text


for message in st.session_state['message_history']: 
    with st.chat_message(message['role']):
        st.markdown(message['content'])
    
user_input = st.chat_input("Type here...")    

if user_input: 
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
     
    
    CONFIG = {
        'configurable': {'thread_id': st.session_state['thread_id']},
        'metadata': {
              'thread_id': st.session_state['thread_id']
            },
        'run_name': 'chat_turn' 
        } 
    
     
    with st.chat_message("assistant"):
        ai_response = st.write_stream(
            stream_with_delay((message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config = CONFIG,
                stream_mode='messages'
            )), delay=0.05)
        )   
        
        st.session_state['message_history'].append({'role': 'assistant', 'content': ai_response})     