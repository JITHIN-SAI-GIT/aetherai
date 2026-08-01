from __future__ import annotations
import copy
import logging
from typing import Protocol, Optional, Dict, Any, List, runtime_checkable
from bson import ObjectId
from .models import MemoryItem, MemoryType
from app.db.repositories.collections import MemoryRepository, PreferenceRepository

logger = logging.getLogger("memory.storage")


@runtime_checkable
class MemoryStorage(Protocol):
    async def get(self, user_id: str, key: str) -> Optional[Any]: ...
    async def set(self, user_id: str, key: str, value: Any) -> None: ...
    async def delete(self, user_id: str, key: str) -> None: ...
    async def clear_user(self, user_id: str) -> None: ...
    async def export(self, user_id: str) -> Dict[str, Any]: ...
    async def save_item(self, item: MemoryItem) -> None: ...
    async def get_items(self, user_id: str, memory_type: Optional[MemoryType] = None) -> List[MemoryItem]: ...


class MongoStorage:
    """
    MongoDB-backed storage for Memory and Preferences.
    Replaces the previous mock/in-memory implementations.
    """
    def __init__(self):
        self.memory_repo = MemoryRepository()
        self.pref_repo = PreferenceRepository()

    async def get(self, user_id: str, key: str) -> Optional[Any]:
        doc = await self.pref_repo.find_one({"user_id": user_id, "key": key})
        if doc:
            return doc.get("value")
        return None

    async def set(self, user_id: str, key: str, value: Any) -> None:
        await self.pref_repo.update_one(
            {"user_id": user_id, "key": key},
            {"user_id": user_id, "key": key, "value": value},
            upsert=True
        )

    async def delete(self, user_id: str, key: str) -> None:
        await self.pref_repo.delete_one({"user_id": user_id, "key": key})
        await self.memory_repo.delete_one({"user_id": user_id, "id": key}) # Just in case

    async def clear_user(self, user_id: str) -> None:
        await self.pref_repo.delete_many({"user_id": user_id})
        await self.memory_repo.delete_many({"user_id": user_id})

    async def export(self, user_id: str) -> Dict[str, Any]:
        prefs = await self.pref_repo.find_many({"user_id": user_id})
        export_data = {p["key"]: p.get("value") for p in prefs}
        return export_data

    async def save_item(self, item: MemoryItem) -> None:
        await self.memory_repo.update_one(
            {"id": item.id, "user_id": item.user_id},
            item.model_dump(),
            upsert=True
        )

    async def get_items(
        self, user_id: str, memory_type: Optional[MemoryType] = None
    ) -> List[MemoryItem]:
        query = {"user_id": user_id}
        if memory_type is not None:
            query["memory_type"] = memory_type.value
            
        docs = await self.memory_repo.find_many(query)
        # Re-construct MemoryItem explicitly checking for missing fields
        # if the db schema has some legacy data
        return [MemoryItem(**doc) for doc in docs]

# Expose MongoStorage as the default MockStorage name to avoid breaking existing imports
# (or we could update all imports, but alias is safer for now)
MockStorage = MongoStorage
