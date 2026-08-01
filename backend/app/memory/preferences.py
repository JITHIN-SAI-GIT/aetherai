import logging
from datetime import datetime
from typing import Any, Optional
from .schema import UserPreferences, PreferenceVersion
from .storage import MemoryStorage

logger = logging.getLogger("memory.preferences")

_PREFS_KEY = "__preferences__"


class PreferencesManager:
    """
    Versioned preference storage with conflict detection and overwrite policy.
    Every update preserves the previous value for audit/rollback purposes.
    """

    def __init__(self, storage: MemoryStorage):
        self._storage = storage

    async def load(self, user_id: str) -> UserPreferences:
        raw = await self._storage.get(user_id, _PREFS_KEY)
        if raw:
            return UserPreferences(**raw)
        return UserPreferences(user_id=user_id)

    async def set(self, user_id: str, key: str, value: Any) -> PreferenceVersion:
        prefs = await self.load(user_id)
        existing = prefs.preferences.get(key)

        if existing and existing.value == value:
            logger.debug("No conflict — value unchanged", extra={"key": key})
            return existing

        version = PreferenceVersion(
            value=value,
            previous_value=existing.value if existing else None,
            version=(existing.version + 1) if existing else 1,
            updated_at=datetime.utcnow(),
        )
        prefs.preferences[key] = version
        await self._storage.set(user_id, _PREFS_KEY, prefs.model_dump())

        logger.info("Preference updated", extra={
            "user_id": user_id, "key": key,
            "version": version.version,
            "conflict": existing is not None,
        })
        return version

    async def get(self, user_id: str, key: str) -> Optional[Any]:
        prefs = await self.load(user_id)
        ver = prefs.preferences.get(key)
        return ver.value if ver else None

    async def delete_key(self, user_id: str, key: str) -> None:
        prefs = await self.load(user_id)
        prefs.preferences.pop(key, None)
        await self._storage.set(user_id, _PREFS_KEY, prefs.model_dump())

    async def all_preferences(self, user_id: str) -> dict:
        prefs = await self.load(user_id)
        return {k: v.value for k, v in prefs.preferences.items()}
