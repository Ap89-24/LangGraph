import streamlit as st 
from chatbot_backend import chatbot
from langchain_core.messages import HumanMessage
import time
  
CONFIG = {'configurable': {'thread_id': 'thread-1'}}    
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []   


def stream_with_delay(chunks, delay=0.02):
    for chunk in chunks:
        for word in chunk.split(" "):
            yield word + " "
            time.sleep(delay) 

for message in st.session_state['message_history']: 
    with st.chat_message(message['role']):
        st.text(message['content'])
    
user_input = st.chat_input("Type here...")    

if user_input: 
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message("user"):
        st.text(user_input)
     
    
    
     
    with st.chat_message("assistant"):
        ai_response = st.write_stream(
            stream_with_delay((message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config = {'configurable': {'thread_id': 'thread-1'}},
                stream_mode='messages'
            )), delay=0.03)
        )   
        
        st.session_state['message_history'].append({'role': 'assistant', 'content': ai_response})     