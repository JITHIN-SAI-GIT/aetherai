import logging
from app.db.mongo import get_db

logger = logging.getLogger("db.indexes")

async def setup_indexes():
    """
    Creates standard indexes for MongoDB Atlas collections.
    """
    try:
        db = get_db()
    except RuntimeError as e:
        logger.warning(f"Skipping index setup: {e}")
        return
    logger.info("Setting up MongoDB indexes...")

    try:
        # Conversations
        await db.conversations.create_index("user_id")
        await db.conversations.create_index("created_at")
        await db.conversations.create_index("updated_at")
        await db.conversations.create_index("session_id")
        
        # Messages
        await db.messages.create_index("conversation_id")
        await db.messages.create_index("user_id")
        await db.messages.create_index("created_at")
        
        # Memory
        await db.memory.create_index("user_id")
        await db.memory.create_index("key")
        
        # Preferences
        await db.preferences.create_index("user_id")
        await db.preferences.create_index("key")
        
        # Providers
        await db.providers.create_index("provider")
        
        # Sessions
        await db.sessions.create_index("session_id")
        await db.sessions.create_index("user_id")
        
        logger.info("Successfully created standard MongoDB indexes.")
        
        # Verify Vector Search Index (Atlas specific)
        try:
            # listSearchIndexes is not universally supported on all local MongoDBs, 
            # but works on Atlas
            cursor = db.memory.list_search_indexes()
            indexes = await cursor.to_list(length=100)
            has_vector = any(idx.get("name") == "vector_index" for idx in indexes)
            if not has_vector:
                logger.warning("Atlas Vector Search index 'vector_index' not found on 'memory' collection. "
                               "Falling back to metadata semantic search.")
            else:
                logger.info("Atlas Vector Search index verified.")
        except Exception as e:
            logger.warning(f"Could not verify Atlas Vector Search index (maybe not on Atlas?): {e}. "
                           "Falling back to metadata semantic search.")

    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        # We don't raise here because we might not have sufficient permissions
        # or the collections might not be fully initialized depending on atlas tier.
