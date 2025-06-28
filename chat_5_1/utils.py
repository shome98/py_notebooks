# utils.py
from datetime import datetime
from pymongo import MongoClient
from passlib.hash import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.chatbot_db
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

def save_message(email, message, is_user=True):
    messages_collection.insert_one({
        "email": email,
        "text": message,
        "is_user": is_user,
        "timestamp": datetime.utcnow()
    })

def get_messages(email):
    return list(messages_collection.find({"email": email}, sort=[("timestamp", 1)]))