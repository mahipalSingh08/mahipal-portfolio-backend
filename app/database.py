import logging

# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = None
db = None


async def connect_to_mongo():
    global client, db
    if not settings.mongodb_uri:
        if settings.is_production:
            raise RuntimeError("MONGODB_URI is required in production.")
        logger.error("MONGODB_URI is not set.")
        return

    try:
        client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
        db = client[settings.mongodb_database]
        await client.admin.command("ping")
        await db.auth_sessions.create_index("expires_at", expireAfterSeconds=0)
        logger.info("Connected to MongoDB database '%s'.", settings.mongodb_database)
    except Exception:
        client = None
        db = None
        logger.exception("Could not connect to MongoDB.")
        raise


async def close_mongo_connection():
    global client
    if client:
        client.close()
        logger.info("Closed MongoDB connection.")


def get_database():
    return db
