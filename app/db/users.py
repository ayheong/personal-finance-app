from pymongo.errors import DuplicateKeyError

from .db import db
from bson.objectid import ObjectId

users_collection = db["users"]

def create_user(username, email, password_hash):
    user = {
        "username": username,
        "email": email,
        "password_hash": password_hash
    }
    try:
        users_collection.insert_one(user)
    except DuplicateKeyError:
        raise ValueError("Username or email already exists")

def get_user_by_username(username):
    try:
        return users_collection.find_one({"username": username})
    except Exception as e:
        print(f"Error fetching user by username: {e}")
        return None

def get_user_by_id(user_id):
    try:
        return users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        print(f"Error fetching user by id: {e}")
        return None