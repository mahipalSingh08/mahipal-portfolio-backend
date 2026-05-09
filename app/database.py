import os
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI
MONGODB_URI = os.getenv("MONGODB_URI")

client = None
db = None

async def connect_to_mongo():
    global client, db
    if MONGODB_URI:
        try:
            client = AsyncIOMotorClient(MONGODB_URI)
            # Use a default database name 'portfolio'
            db = client.portfolio
            print("Connected to MongoDB!")
        except Exception as e:
            print(f"Could not connect to MongoDB: {e}")
    else:
        print("MONGODB_URI is not set in environment variables.")

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("Closed MongoDB connection.")

def get_database():
    return db
