# FILE: chat_5_1/app.py
import streamlit as st
import requests
import json
import os
import hashlib
from dotenv import load_dotenv
from datetime import datetime
from utils import get_user, create_user, verify_password, save_message_pair, get_messages

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if api_key is None:
    raise ValueError("OPENROUTER_API_KEY not found in .env")

# --- Configuration ---
OPENROUTER_API_KEY = api_key
YOUR_SITE_URL = "https://your-site.com "
YOUR_SITE_NAME = "MyAIApp"

st.set_page_config(
    page_title="🤖 AI Chatbot",
    page_icon="🤖"
)

# --- Session State Setup ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'email' not in st.session_state:
    st.session_state.email = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []

def generate_id(email, timestamp):
    """Generate a unique ID based on timestamp and email"""
    timestamp_str = timestamp.strftime("%Y%m%d%H%M%S%f")
    combined = f"{timestamp_str}_{email}"
    return hashlib.md5(combined.encode()).hexdigest()

def convert_messages_to_txt(messages):
    """Convert messages to plain text format"""
    output = ""
    for msg in messages:
        role = msg["role"].capitalize()
        content = msg["content"].strip()
        output += f"{role}: {content}\n\n"
    return output.strip()

# --- Function to stream AI response ---
def stream_ai_response(user_message):
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
            *[{
                "role": msg["role"],
                "content": msg["content"]
            } for msg in st.session_state.messages]
        ],
        "temperature": 0.7,
        "stream": True
    }

    def generate():
        with requests.post(url, headers=headers, json=data, stream=True) as response:
            try:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8").strip()
                        if decoded_line.startswith("data: "):
                            json_data = decoded_line[6:]
                            if json_data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(json_data)
                                delta = chunk["choices"][0]["delta"].get("content")
                                if delta:
                                    yield delta
                            except json.JSONDecodeError:
                                continue
            except requests.exceptions.RequestException as e:
                yield f"\n\n⚠️ Error: {e}"

    return generate()

# --- Login Page ---
def login_page():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_password(email, password):
            st.session_state.logged_in = True
            st.session_state.email = email
            st.session_state.messages = get_messages(email)
            st.rerun()
        else:
            st.error("Invalid credentials")

# --- Register Page ---
def register_page():
    st.title("📝 Register")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if create_user(email, password):
            st.success("Registered successfully! Please log in.")
        else:
            st.error("Email already taken.")

# --- Chat Page ---
def chat_page():
    with st.sidebar:
        st.markdown(f"👤 Logged in as `{st.session_state.email}`")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.email = ""
            st.session_state.messages = []
            st.rerun()
        st.markdown("---")
        st.markdown("🧠 Powered by DeepSeek via OpenRouter")
        st.markdown("---")
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 TXT",
                data=convert_messages_to_txt(st.session_state.messages),
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        with col2:
            st.download_button(
                "📥 JSON",
                data=json.dumps(st.session_state.messages, indent=2, ensure_ascii=False),
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )

    st.title("🤖 AI Chatbot")

    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle new input
    if prompt := st.chat_input("Ask something..."):
        # Add user message temporarily
        timestamp = datetime.utcnow()
        message_id = generate_id(st.session_state.email, timestamp)
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        st.session_state.messages.append({
            "id": message_id,
            "role": "user",
            "content": prompt,
            "time": time_str
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🧠 Thinking...")
            full_response = ""

            for chunk in stream_ai_response(prompt):
                full_response += chunk
                message_placeholder.markdown(full_response + "|")

            message_placeholder.markdown(full_response)

        # Save both messages together
        st.session_state.messages.append({
            "id": generate_id(st.session_state.email, datetime.utcnow()),
            "role": "assistant",
            "content": full_response,
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Save to database as a message pair
        save_message_pair(
            st.session_state.email,
            prompt,
            full_response,
            timestamp
        )

# --- Routing ---
if not st.session_state.logged_in:
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Login", "Register"])
    if page == "Login":
        login_page()
    elif page == "Register":
        register_page()
else:
    chat_page()