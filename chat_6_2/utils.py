# FILE: chat_5_1/utils.py
# utils.py
from datetime import datetime
import hashlib
from pymongo import MongoClient
from passlib.hash import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.chatbot_db_7pm29jun25
users_collection = db.users
messages_collection = db.messages

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

def save_message(email, message, is_user=True, timestamp=None):
    if timestamp is None:
        timestamp = datetime.utcnow()
    messages_collection.insert_one({
        "email": email,
        "text": message,
        "is_user": is_user,
        "timestamp": timestamp
    })

def get_messages(email):
    messages = list(messages_collection.find({"email": email}, sort=[("timestamp", 1)]))
    converted = []
    for msg in messages:
        role = "user" if msg["is_user"] else "assistant"
        message_id = generate_id(msg["email"], msg["timestamp"])
        converted.append({
            "id": message_id,
            "role": role,
            "content": msg["text"],
            "time": msg["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        })
    return converted

def generate_id(email, timestamp):
    """Generate a unique ID based on timestamp and email"""
    timestamp_str = timestamp.strftime("%Y%m%d%H%M%S%f")
    combined = f"{timestamp_str}_{email}"
    return hashlib.md5(combined.encode()).hexdigest()