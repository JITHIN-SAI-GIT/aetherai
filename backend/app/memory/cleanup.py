import logging
import time
from datetime import datetime
from typing import List
from .models import MemoryItem, MemoryClassification
from .storage import MemoryStorage

logger = logging.getLogger("memory.cleanup")


class MemoryCleanup:
    """
    Prunes expired, ignored, and over-budget memory items.
    Respects privacy: never deletes without explicit call.
    """

    def __init__(self, storage: MemoryStorage, max_items_per_user: int = 500):
        self._storage = storage
        self._max_items = max_items_per_user
        self._cleanup_count = 0

    async def prune_expired(self, user_id: str) -> int:
        items = await self._storage.get_items(user_id)
        now = datetime.utcnow()
        expired = [
            i for i in items
            if i.expires_at and i.expires_at < now
        ]
        for item in expired:
            await self._storage.delete(user_id, item.id)
        self._cleanup_count += len(expired)
        logger.info("Pruned expired items", extra={"user_id": user_id, "count": len(expired)})
        return len(expired)

    async def prune_ignored(self, user_id: str) -> int:
        items = await self._storage.get_items(user_id)
        ignored = [i for i in items if i.classification == MemoryClassification.IGNORE]
        for item in ignored:
            await self._storage.delete(user_id, item.id)
        self._cleanup_count += len(ignored)
        logger.info("Pruned ignored items", extra={"user_id": user_id, "count": len(ignored)})
        return len(ignored)

    def cleanup_count(self) -> int:
        return self._cleanup_count
