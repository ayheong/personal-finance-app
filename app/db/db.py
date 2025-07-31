from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os

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

