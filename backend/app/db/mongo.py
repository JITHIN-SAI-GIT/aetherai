import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import get_settings

logger = logging.getLogger("db.mongo")

class MongoDBManager:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    @classmethod
    async def connect(cls):
        settings = get_settings()
        logger.info("Connecting to MongoDB...")
        try:
            # Short timeout to fail fast on invalid DNS or unreachability
            cls.client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
            cls.db = cls.client[settings.database_name]
            # Verify connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB Atlas database: {settings.database_name}")
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                logger.error(f"MongoDB Network Timeout or Atlas Unavailable: {e}")
            elif "auth" in error_msg or "authentication" in error_msg:
                logger.error("MongoDB Authentication Failure: Invalid credentials.")
            elif "dns" in error_msg or "configuration" in error_msg:
                logger.error(f"MongoDB DNS or Configuration Failure: {e}")
            else:
                logger.error(f"Failed to connect to MongoDB: {e}")
            
            # We don't raise here if the system is designed to fail gracefully,
            # but since FastAPI startup requires a working connection for this tier,
            # we should raise to prevent a zombie process.
            # However, the user said "Fail gracefully with a clear error if MongoDB is unavailable."
            # So maybe we just log and leave cls.client as None? Let's not raise, let's gracefully fail.
            cls.client = None
            cls.db = None
            logger.error("Application starting in degraded mode without MongoDB connection.")

    @classmethod
    async def disconnect(cls):
        if cls.client:
            logger.info("Disconnecting from MongoDB...")
            cls.client.close()
            logger.info("Disconnected from MongoDB.")

def get_db():
    if MongoDBManager.db is None:
        raise RuntimeError("MongoDB is not initialized.")
    return MongoDBManager.db
