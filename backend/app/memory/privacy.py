import logging
from typing import Any, Dict
from .storage import MemoryStorage
from .exceptions import MemoryPrivacyError

logger = logging.getLogger("memory.privacy")


class PrivacyManager:
    """
    Implements privacy controls: delete, export, and clear session.
    All destructive operations require explicit confirmation to prevent accidents.
    """

    def __init__(self, storage: MemoryStorage):
        self._storage = storage

    async def delete_all(self, user_id: str, confirmed: bool = False) -> None:
        if not confirmed:
            raise MemoryPrivacyError(
                "delete_all requires confirmed=True to prevent accidental deletion."
            )
        await self._storage.clear_user(user_id)
        logger.info("All memory deleted", extra={"user_id": user_id})

    async def delete_key(self, user_id: str, key: str) -> None:
        await self._storage.delete(user_id, key)
        logger.info("Memory key deleted", extra={"user_id": user_id, "key": key})

    async def export_profile(self, user_id: str) -> Dict[str, Any]:
        data = await self._storage.export(user_id)
        logger.info("Profile exported", extra={"user_id": user_id})
        return {
            "user_id": user_id,
            "profile": data.get("__profile__"),
            "preferences": data.get("__preferences__"),
        }

    async def export_all(self, user_id: str) -> Dict[str, Any]:
        data = await self._storage.export(user_id)
        logger.info("Full export complete", extra={"user_id": user_id})
        return {"user_id": user_id, "data": data}
