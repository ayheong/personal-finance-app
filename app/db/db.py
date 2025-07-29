from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os
import pandas as pd

# Locate and load .env from project root
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# Get Mongo URI
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env")

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)
db = client["personal_finance"]
collection = db["transactions"]

def save_transactions(df: pd.DataFrame, user_id: str = "default_user"):
    if df.empty:
        print("DataFrame is empty. Skipping save.")
        return

    df["user_id"] = user_id
    records = df.to_dict(orient="records")
    collection.insert_many(records)
    print(f"Inserted {len(records)} transactions for user {user_id}")

def get_transactions(user_id):
    query = {"user_id": user_id}
    results = list(collection.find(query, {"_id": 0}))
    return results