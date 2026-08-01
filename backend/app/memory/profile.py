import logging
from typing import Optional
from .schema import UserProfile
from .storage import MemoryStorage

logger = logging.getLogger("memory.profile")

_PROFILE_KEY = "__profile__"


class ProfileManager:
    """Loads and updates structured user profiles from storage."""

    def __init__(self, storage: MemoryStorage):
        self._storage = storage

    async def load(self, user_id: str) -> UserProfile:
        raw = await self._storage.get(user_id, _PROFILE_KEY)
        if raw:
            return UserProfile(**raw)
        return UserProfile(user_id=user_id)

    async def update(self, user_id: str, **kwargs) -> UserProfile:
        profile = await self.load(user_id)
        updated = profile.model_copy(update=kwargs)
        await self._storage.set(user_id, _PROFILE_KEY, updated.model_dump())
        logger.info("Profile updated", extra={"user_id": user_id, "fields": list(kwargs.keys())})
        return updated

    async def apply_memory_items(self, user_id: str, items) -> UserProfile:
        """Apply a list of MemoryItems to the profile fields."""
        profile = await self.load(user_id)
        update_fields = {}
        for item in items:
            key = item.key
            if hasattr(profile, key):
                if isinstance(getattr(profile, key), list):
                    current = list(getattr(profile, key))
                    if item.value not in current:
                        current.append(item.value)
                    update_fields[key] = current
                else:
                    update_fields[key] = item.value
        if update_fields:
            return await self.update(user_id, **update_fields)
        return profile
