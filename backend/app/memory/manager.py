import logging
from typing import List, Dict, Any, Optional
from .storage import MemoryStorage
from .extractor import FactExtractor
from .classifier import MemoryClassifier
from .summarizer import ConversationSummarizer
from .profile import ProfileManager
from .preferences import PreferencesManager
from .session import SessionMemory
from .cleanup import MemoryCleanup
from .privacy import PrivacyManager
from .metrics import MemoryMetrics
from .models import ExtractionResult, ConversationSummary
from .schema import UserProfile

logger = logging.getLogger("memory.manager")


class MemoryManager:
    """
    Single public interface for the entire memory subsystem.
    All pipeline components interact exclusively through this class.
    """

    def __init__(
        self,
        storage: MemoryStorage,
        extractor: FactExtractor,
        summarizer: ConversationSummarizer,
        session: SessionMemory,
        profile_mgr: ProfileManager,
        prefs_mgr: PreferencesManager,
        cleanup: MemoryCleanup,
        privacy: PrivacyManager,
        metrics: MemoryMetrics,
    ):
        self._storage = storage
        self._extractor = extractor
        self._summarizer = summarizer
        self._session = session
        self._profile_mgr = profile_mgr
        self._prefs_mgr = prefs_mgr
        self._cleanup = cleanup
        self._privacy = privacy
        self._metrics = metrics

    async def load(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Load full context for the pipeline: profile + preferences + session."""
        self._metrics.record_load()
        profile = await self._profile_mgr.load(user_id)
        preferences = await self._prefs_mgr.all_preferences(user_id)
        session_messages = self._session.get_messages(session_id)

        logger.info("Memory loaded", extra={"user_id": user_id, "session_id": session_id})
        return {
            "profile": profile.model_dump(),
            "preferences": preferences,
            "session_messages": session_messages,
        }

    async def extract(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_turn: int = 0,
    ) -> ExtractionResult:
        """Extract structured facts from raw messages without storing raw text."""
        result = self._extractor.extract(messages, user_id, session_turn)
        self._metrics.record_extraction(len(result.items))
        logger.info("Facts extracted", extra={
            "user_id": user_id, "count": len(result.items)
        })
        return result

    async def save(self, user_id: str, result: ExtractionResult) -> None:
        """Persist extracted facts and update the user profile."""
        self._metrics.record_save()
        for item in result.items:
            await self._storage.save_item(item)
        await self._profile_mgr.apply_memory_items(user_id, result.items)
        logger.info("Memory saved", extra={"user_id": user_id, "items": len(result.items)})

    async def summarize(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_id: str,
    ) -> Optional[ConversationSummary]:
        if not self._summarizer.should_summarize(messages):
            return None
        summary = await self._summarizer.summarize_async(messages, user_id, session_id)
        self._metrics.record_summary()
        return summary

    async def cleanup(self, user_id: str) -> int:
        expired = await self._cleanup.prune_expired(user_id)
        ignored = await self._cleanup.prune_ignored(user_id)
        total = expired + ignored
        self._metrics.record_cleanup(total)
        return total

    async def delete(self, user_id: str, confirmed: bool = False) -> None:
        await self._privacy.delete_all(user_id, confirmed=confirmed)

    async def clear_session(self, session_id: str) -> None:
        self._session.clear(session_id)

    async def export(self, user_id: str) -> Dict[str, Any]:
        return await self._privacy.export_all(user_id)

    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics.snapshot()
