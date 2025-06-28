import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from utils import get_user, create_user, verify_password, save_message, get_messages
import emoji

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if api_key is None:
    raise ValueError("OPENROUTER_API_KEY not found in .env")

# --- Configuration ---
OPENROUTER_API_KEY = api_key
YOUR_SITE_URL = "https://your-site.com "
YOUR_SITE_NAME = "MyAIApp"

# --- Session State Setup ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'email' not in st.session_state:
    st.session_state.email = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- Inject ChatGPT-Like Styles ---
st.markdown("""
<style>
    body {
        background-color: #111111;
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .sidebar .sidebar-content {
        background-color: #1a1a1a;
        padding: 1rem;
        border-right: 1px solid #333;
    }
    .stTextInput input {
        background-color: #222222;
        color: white;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 0.75rem;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        max-width: 80%;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    .stChatMessageUser {
        background-color: #2b6cb0;
        align-self: flex-end;
        border-radius: 16px 4px 16px 16px;
        color: white;
    }
    .stChatMessageAssistant {
        background-color: #2a2a2a;
        align-self: flex-start;
        border-radius: 4px 16px 16px 16px;
        color: white;
    }
    .thinking {
        display: inline-block;
        width: 12px;
        height: 12px;
        margin: 0 2px;
        background-color: #666;
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }
    @keyframes typing {
        0% { transform: translateY(0); opacity: 0.4; }
        50% { transform: translateY(-5px); opacity: 1; }
        100% { transform: translateY(0); opacity: 0.4; }
    }
</style>
""", unsafe_allow_html=True)

# --- Function to stream AI response ---
def stream_ai_response(user_message):
    url = "https://openrouter.ai/api/v1/chat/completions "
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
        st.markdown("### 🤖 MyAIApp")
        st.markdown("---")
        st.markdown(f"👤 {st.session_state.email}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.email = ""
            st.session_state.messages = []
            st.rerun()
        st.markdown("---")
        st.markdown("🧠 Powered by DeepSeek via OpenRouter")

    st.markdown("### 💬 Chat with AI")
    st.markdown("---")

    # Display existing messages
    for message in st.session_state.messages:
        role = "User" if message["is_user"] else "Assistant"
        bubble_class = "stChatMessageUser" if message["is_user"] else "stChatMessageAssistant"
        st.markdown(f"""
        <div class="stChatMessage {bubble_class}">
            <strong>{role}:</strong> {emoji.emojize(message["text"])}
        </div>
        """, unsafe_allow_html=True)

    # Input area
    user_input = st.text_area("You:", key="input", height=100, placeholder="Ask me anything...")
    if st.button("Send"):
        if user_input.strip():
            # Add user message
            st.session_state.messages.append({"text": user_input, "is_user": True})
            save_message(st.session_state.email, user_input, is_user=True)

            # Get AI response
            with st.spinner("🧠 Thinking..."):
                full_response = ""
                message_placeholder = st.empty()
                for chunk in stream_ai_response(user_input):
                    full_response += chunk
                    message_placeholder.markdown(f"""
                    <div class="stChatMessage stChatMessageAssistant">
                        <strong>Assistant:</strong> {full_response}▌
                    </div>
                    """, unsafe_allow_html=True)

                # Final update
                message_placeholder.markdown(f"""
                <div class="stChatMessage stChatMessageAssistant">
                    <strong>Assistant:</strong> {full_response}
                </div>
                """, unsafe_allow_html=True)

            # Save AI response
            st.session_state.messages.append({"text": full_response, "is_user": False})
            save_message(st.session_state.email, full_response, is_user=False)

            st.rerun()

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