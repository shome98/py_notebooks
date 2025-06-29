import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from utils import (
    get_user, create_user, verify_password,
    create_chat_session, get_all_chats, get_chat_by_id,
    update_chat_messages, update_chat_title, add_tag_to_chat, delete_chat
)

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
api_url = os.getenv("OPENROUTER_URL")

if api_key is None:
    raise ValueError("OPENROUTER_API_KEY not found in .env")
if api_url is None:
    raise ValueError("OPENROUTER_URL not found in .env")

# --- Configuration ---
OPENROUTER_API_KEY = api_key
YOUR_SITE_URL = "https://your-site.com"
YOUR_SITE_NAME = "MyAIApp"

# Set page config
st.set_page_config(page_title="🤖 AI Chatbot", layout="wide")

# Hide Streamlit menu and footer
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Session State Setup ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'email' not in st.session_state:
    st.session_state.email = ""
if 'chats' not in st.session_state:
    st.session_state.chats = []
if 'current_chat' not in st.session_state:
    st.session_state.current_chat = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

# --- Function to stream AI response ---
def stream_ai_response(user_message):
    url = api_url
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
            *[{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
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
                        if decoded_line.startswith(" "):
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

# --- Auto Title Generation ---
def generate_chat_title(first_message):
    url = api_url
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": YOUR_SITE_URL,
        "X-Title": YOUR_SITE_NAME
    }

    data = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {"role": "system", "content": "Generate a concise and descriptive title for this conversation:"},
            {"role": "user", "content": first_message}
        ],
        "temperature": 0.3,
        "max_tokens": 30
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except:
        return "New Chat"

# --- Login Page ---
def login_page():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_password(email, password):
            st.session_state.logged_in = True
            st.session_state.email = email
            st.session_state.chats = get_all_chats(email)
            if st.session_state.chats:
                latest_chat = st.session_state.chats[0]
                st.session_state.current_chat = latest_chat["chat_id"]
                st.session_state.messages = latest_chat.get("messages", [])
            else:
                chat_id, title = create_chat_session(email)
                st.session_state.current_chat = chat_id
                st.session_state.chats = get_all_chats(email)
                st.session_state.messages = []
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
        st.subheader("💬 Your Chats")

        if st.button("➕ New Chat"):
            chat_id, title = create_chat_session(st.session_state.email)
            st.session_state.current_chat = chat_id
            st.session_state.chats = get_all_chats(st.session_state.email)

            if st.session_state.messages:
                first_message = st.session_state.messages[0]["content"]
                new_title = generate_chat_title(first_message)
                update_chat_title(chat_id, new_title)
                st.session_state.chats = get_all_chats(st.session_state.email)

            st.rerun()

        for chat in st.session_state.chats:
            chat_id = chat["chat_id"]
            current_title = chat["title"]

            cols = st.columns([0.8, 0.2])
            with cols[0]:
                new_title = st.text_input("Rename", value=current_title, key=f"rename_{chat_id}", label_visibility="collapsed")
            if new_title != current_title:
                update_chat_title(chat_id, new_title)
                st.rerun()

            with cols[1]:
                if st.button("🗑️", key=f"del_{chat_id}"):
                    delete_chat(chat_id)
                    st.session_state.chats = get_all_chats(st.session_state.email)
                    if st.session_state.chats:
                        st.session_state.current_chat = st.session_state.chats[0]["chat_id"]
                        st.session_state.messages = st.session_state.chats[0].get("messages", [])
                    else:
                        st.session_state.current_chat = None
                        st.session_state.messages = []
                    st.rerun()

        st.markdown("---")
        st.markdown(f"👤 Logged in as `{st.session_state.email}`")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.email = ""
            st.session_state.messages = []
            st.session_state.chats = []
            st.session_state.current_chat = None
            st.rerun()

        st.markdown("---")
        st.markdown("🧠 Powered by DeepSeek via OpenRouter")

        # Export options
        if st.session_state.current_chat and st.session_state.messages:
            chat_title = next((c["title"] for c in st.session_state.chats if c["chat_id"] == st.session_state.current_chat), "Chat")

            txt_data = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.messages])
            st.download_button("📄 Export as .txt", txt_data, file_name=f"{chat_title}.txt")

            json_data = json.dumps(st.session_state.messages, indent=2)
            st.download_button("📦 Export as .json", json_data, file_name=f"{chat_title}.json")

        # Dark/Light Mode Toggle
        st.markdown("---")
        if st.checkbox("🌙 Dark Mode", value=st.session_state.dark_mode):
            st.session_state.dark_mode = True
        else:
            st.session_state.dark_mode = False

        # Footer from knowledge base
        st.markdown("---")
        st.markdown("""
        **Your-Site.Com/Fluidsoft, Inc.**  
        P.O. Box 535 | Funkstown, MD 21734  
        info@your-site.com  
        Copyright © 1996-2025 Your-Site.Com
        """)

    st.title("🤖 AI Chatbot")

    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle new input
    if prompt := st.chat_input("Ask something..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        update_chat_messages(st.session_state.current_chat, st.session_state.messages)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🧠 Thinking...")
            full_response = ""

            for chunk in stream_ai_response(prompt):
                print("response is ",chunk)
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        update_chat_messages(st.session_state.current_chat, st.session_state.messages)

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