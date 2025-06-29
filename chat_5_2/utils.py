# utils.py
from pymongo import MongoClient
from passlib.hash import bcrypt
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.chatbot_db_2
users_collection = db.users
chat_sessions_collection = db.chat_sessions

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

def create_chat_session(email):
    chat_id = str(uuid.uuid4())
    default_title = "New Chat"
    chat_sessions_collection.insert_one({
        "email": email,
        "chat_id": chat_id,
        "title": default_title,
        "tags": [],
        "messages": [],
        "timestamp": datetime.utcnow()
    })
    return chat_id, default_title

def get_all_chats(email):
    return list(chat_sessions_collection.find({"email": email}, sort=[("timestamp", -1)]))

def get_chat_by_id(chat_id):
    return chat_sessions_collection.find_one({"chat_id": chat_id})

def update_chat_messages(chat_id, messages):
    chat_sessions_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"messages": messages}}
    )

def update_chat_title(chat_id, new_title):
    chat_sessions_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"title": new_title}}
    )

def add_tag_to_chat(chat_id, tag):
    chat_sessions_collection.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"tags": tag.lower()}}
    )

def delete_chat(chat_id):
    chat_sessions_collection.delete_one({"chat_id": chat_id})