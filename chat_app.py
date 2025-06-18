import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key=os.getenv("OPENROUTER_API_KEY")

if api_key is None:
    raise ValueError("POSTGRES_URI ot found in .env")
# --- Configuration ---
OPENROUTER_API_KEY = api_key
YOUR_SITE_URL = "https://your-site.com"   # Optional
YOUR_SITE_NAME = "MyAIApp"                # Optional

# --- Function to get AI response ---
def get_ai_response(user_message):
    url = "https://openrouter.ai/api/v1/chat/completions" 

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": YOUR_SITE_URL,
        "X-Title": YOUR_SITE_NAME
    }

    data = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            *[{"role": "user" if msg["is_user"] else "assistant", "content": msg["text"]} 
              for msg in st.session_state.messages]
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        return f"API Error: {e}"
    except KeyError:
        return "Failed to parse AI response."

# --- Initialize session state for chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Streamlit UI ---
st.set_page_config(page_title="AI Chatbot", layout="centered")
st.title("🤖 AI Chatbot")

# Display existing messages
for message in st.session_state.messages:
    with st.chat_message("user" if message["is_user"] else "assistant"):
        st.markdown(message["text"])

# Handle new user input
if prompt := st.chat_input("Ask something..."):
    # Add user message to chat history
    st.session_state.messages.append({"text": prompt, "is_user": True})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ai_response = get_ai_response(prompt)
        st.markdown(ai_response)
    
    # Add AI response to chat history
    st.session_state.messages.append({"text": ai_response, "is_user": False})