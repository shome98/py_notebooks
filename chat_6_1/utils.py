# utils.py
from pymongo import MongoClient
from passlib.hash import bcrypt
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- MongoDB Setup ---
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env")

client = MongoClient(MONGO_URI)
db = client.chatbot_db

# Collections
users_collection = db.users
chat_sessions_collection = db.chat_sessions
analytics_collection = db.analytics
admins_collection = db.admins
tags_collection = db.tags

# --- User Auth Functions ---
def get_user(email):
    return users_collection.find_one({"email": email})

def create_user(email, password):
    if get_user(email):
        return False  # User already exists
    hashed_pw = bcrypt.hash(password)
    users_collection.insert_one({
        "email": email,
        "password": hashed_pw
    })
    return True

def verify_password(email, password):
    user = get_user(email)
    if not user:
        return False
    return bcrypt.verify(password, user["password"])

# --- Admin Auth Functions ---
def create_admin(email, password):
    if admins_collection.find_one({"email": email}):
        return False  # Admin already exists
    hashed_pw = bcrypt.hash(password)
    admins_collection.insert_one({
        "email": email,
        "password": hashed_pw
    })
    return True

def verify_admin(email, password):
    admin = admins_collection.find_one({"email": email})
    if not admin:
        return False
    return bcrypt.verify(password, admin["password"])

# --- Chat Session Functions ---
def create_chat_session(email):
    from uuid import uuid4
    chat_id = str(uuid4())
    default_title = "New Chat"
    chat_sessions_collection.insert_one({
        "email": email,
        "chat_id": chat_id,
        "title": default_title,
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

def delete_chat(chat_id):
    chat_sessions_collection.delete_one({"chat_id": chat_id})

# --- Analytics Functions ---
def add_token_usage_record(email, prompt_tokens, completion_tokens):
    record = {
        "email": email,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "timestamp": datetime.utcnow()
    }
    analytics_collection.insert_one(record)

def get_token_usage_by_user(email):
    return list(analytics_collection.find({"email": email}, sort=[("timestamp", 1)]))

def get_monthly_token_usage(email, year=None, month=None):
    match = {"email": email}
    if year and month:
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
        match["timestamp"] = {"$gte": start_date, "$lt": end_date}

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": None,
                "total_prompt_tokens": {"$sum": "$prompt_tokens"},
                "total_completion_tokens": {"$sum": "$completion_tokens"},
                "total_tokens": {"$sum": "$total_tokens"}
            }
        }
    ]
    result = list(analytics_collection.aggregate(pipeline))
    return result[0] if result else {
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_tokens": 0
    }

def get_all_users():
    return list(users_collection.find({}, {"_id": 0, "email": 1}))

def get_all_token_usage():
    return list(analytics_collection.find({}))

def get_chats_by_user(email):
    return list(chat_sessions_collection.find({"email": email}))