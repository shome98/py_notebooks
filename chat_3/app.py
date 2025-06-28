import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from utils import get_user, create_user, verify_password, save_message, get_messages

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

# --- UI Pages ---
def login_page():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_password(email, password):
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def register_page():
    st.title("📝 Register")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if create_user(email, password):
            st.success("Registered successfully! Please log in.")
        else:
            st.error("Email already taken.")

def chat_page():
    st.set_page_config(page_title="🤖 AI Chatbot", layout="centered")
    st.title("🤖 AI Chatbot")

    # Load chat history from MongoDB
    if "messages" not in st.session_state:
        st.session_state.messages = get_messages(st.session_state.email)

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

        # Save user message to MongoDB
        save_message(st.session_state.email, prompt, is_user=True)

        # Get AI response and display it with streaming effect
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🧠 Thinking...")
            full_response = ""

            # Stream response into placeholder
            for chunk in stream_ai_response(prompt):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")  # Show cursor while typing

            # Final update without cursor
            message_placeholder.markdown(full_response)

        # Add AI response to chat history
        st.session_state.messages.append({"text": full_response, "is_user": False})

        # Save assistant message to MongoDB
        save_message(st.session_state.email, full_response, is_user=False)

# --- Streaming AI Response Function ---
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

# --- App Routing ---
if not st.session_state.logged_in:
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Login", "Register"])
    if page == "Login":
        login_page()
    elif page == "Register":
        register_page()
else:
    chat_page()