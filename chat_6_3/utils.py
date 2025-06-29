# FILE: chat_5_1/utils.py
# utils.py
from datetime import datetime
from pymongo import MongoClient
from passlib.hash import bcrypt
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.chatbot_db_4
users_collection = db.users
conversations_collection = db.conversations

def generate_id(email, timestamp):
    """Generate a unique ID based on timestamp and email"""
    timestamp_str = timestamp.strftime("%Y%m%d%H%M%S%f")
    combined = f"{timestamp_str}_{email}"
    return hashlib.md5(combined.encode()).hexdigest()

def get_user(email):
    return users_collection.find_one({"email": email})

def create_user(email, password):
    if get_user(email):
        return False  # User already exists
    hashed_pw = bcrypt.hash(password)
    users_collection.insert_one({"email": email, "password": hashed_pw})
    return True

def verify_password(email, password):
    user = get_user(email)
    if not user:
        return False
    return bcrypt.verify(password, user["password"])

def save_message_pair(email, user_prompt, assistant_reply, timestamp):
    """Save user/assistant message pair in the required format"""
    message_id = generate_id(email, timestamp)
    
    message_entry = {
        "message_id": message_id,
        "user_prompt": user_prompt,
        "assistant_reply": assistant_reply,
        "timestamp": timestamp
    }
    
    # Update the conversation document
    conversations_collection.update_one(
        {"email": email},
        {
            "$push": {"messages": message_entry},
            "$setOnInsert": {"created_at": timestamp},
            "$set": {"updated_at": timestamp}
        },
        upsert=True
    )

def get_messages(email):
    """Retrieve and format messages for session state"""
    conversation = conversations_collection.find_one(
        {"email": email},
        {"_id": 0, "messages": 1}
    )
    
    if not conversation or "messages" not in conversation:
        return []
    
    formatted_messages = []
    for msg in conversation["messages"]:
        # Add user message
        formatted_messages.append({
            "id": msg["message_id"],
            "role": "user",
            "content": msg["user_prompt"],
            "time": msg["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Add assistant message
        formatted_messages.append({
            "id": generate_id(email, msg["timestamp"]),
            "role": "assistant",
            "content": msg["assistant_reply"],
            "time": msg["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return formatted_messages