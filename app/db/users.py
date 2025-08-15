from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

from .db import db

users_collection = db["users"]


def create_user(username: str, email: str, password_hash: str) -> None:
    """Insert a new user into the database."""
    user = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
    }
    try:
        users_collection.insert_one(user)
    except DuplicateKeyError:
        raise ValueError("Username or email already exists")


def get_user_by_username(username: str) -> dict | None:
    """Retrieve a user document by username."""
    try:
        return users_collection.find_one({"username": username})
    except Exception as e:
        print(f"Error fetching user by username: {e}")
        return None


def get_user_by_id(user_id: str) -> dict | None:
    """Retrieve a user document by ObjectId."""
    try:
        return users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        print(f"Error fetching user by id: {e}")
        return None
