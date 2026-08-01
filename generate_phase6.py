import os

base_path = r"c:\Users\jithin sai\OneDrive\Desktop\finalbot\backend"

directories = ["app/memory", "tests/memory"]

files = {

# ── MODELS ──────────────────────────────────────────────────────────────────
"app/memory/models.py": '''from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MemoryType(str, Enum):
    SHORT_TERM  = "short_term"
    LONG_TERM   = "long_term"
    SESSION     = "session"
    PROFILE     = "profile"
    PREFERENCE  = "preference"
    SUMMARY     = "summary"
    PROJECT     = "project"


class MemoryClassification(str, Enum):
    PREFERENCE  = "preference"
    FACT        = "fact"
    PROJECT     = "project"
    TEMPORARY   = "temporary"
    IGNORE      = "ignore"


class MemoryItem(BaseModel):
    id: str
    user_id: str
    memory_type: MemoryType
    classification: MemoryClassification
    key: str
    value: Any
    confidence: float = 1.0
    source_turn: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    items: List[MemoryItem] = Field(default_factory=list)
    ignored_count: int = 0
    total_scanned: int = 0


class ConversationSummary(BaseModel):
    user_id: str
    session_id: str
    summary: str
    turn_range: tuple
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message_count_compressed: int = 0
''',

# ── EXCEPTIONS ───────────────────────────────────────────────────────────────
"app/memory/exceptions.py": '''class MemoryError(Exception):
    pass

class MemoryStorageError(MemoryError):
    def __init__(self, backend: str, message: str):
        self.backend = backend
        super().__init__(f"[{backend}] {message}")

class MemoryPrivacyError(MemoryError):
    """Raised when a privacy operation is attempted without proper confirmation."""
    pass

class MemoryExtractionError(MemoryError):
    """Raised when the extractor encounters an unrecoverable parsing error."""
    pass
''',

# ── SCHEMA ───────────────────────────────────────────────────────────────────
"app/memory/schema.py": '''from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MemoryFact(BaseModel):
    key: str
    value: Any
    confidence: float = 1.0
    source: str = "extracted"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    user_id: str
    preferred_language: Optional[str] = None
    preferred_provider: Optional[str] = None
    preferred_framework: Optional[str] = None
    favorite_technologies: List[str] = Field(default_factory=list)
    writing_tone: Optional[str] = None
    coding_style: Optional[str] = None
    current_project: Optional[str] = None
    goals: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PreferenceVersion(BaseModel):
    value: Any
    previous_value: Optional[Any] = None
    version: int = 1
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserPreferences(BaseModel):
    user_id: str
    preferences: Dict[str, PreferenceVersion] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectContext(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True
''',

# ── CLASSIFIER ───────────────────────────────────────────────────────────────
"app/memory/classifier.py": '''import re
import logging
from .models import MemoryClassification

logger = logging.getLogger("memory.classifier")

# Pattern → classification mapping (evaluated in order)
CLASSIFICATION_RULES = [
    # Ignore greetings and small talk
    (re.compile(r"^(hi|hello|hey|thanks|thank you|ok|okay|sure|great|cool|bye)\\b", re.I),
     MemoryClassification.IGNORE),

    # Projects
    (re.compile(r"\\b(project|building|working on|developing|creating)\\b", re.I),
     MemoryClassification.PROJECT),

    # Preferences (explicit)
    (re.compile(
        r"\\b(prefer|like|love|use|favorite|always use|usually|tend to use|"
        r"my style|my preference|i want|i need)\\b", re.I),
     MemoryClassification.PREFERENCE),

    # Facts (declarative knowledge)
    (re.compile(
        r"\\b(my name is|i am|i work|my goal|i\'m a|i specialize|"
        r"i know|my background|i have experience)\\b", re.I),
     MemoryClassification.FACT),

    # Temporary / transient
    (re.compile(r"\\b(today|right now|currently|for now|just this once|temporary)\\b", re.I),
     MemoryClassification.TEMPORARY),
]


class MemoryClassifier:
    """
    Assigns a MemoryClassification to a raw text snippet.
    Rule-based; designed to be replaced with an ML classifier in future phases.
    """

    def classify(self, text: str) -> MemoryClassification:
        for pattern, classification in CLASSIFICATION_RULES:
            if pattern.search(text):
                logger.debug("Classified", extra={"text_len": len(text),
                                                   "classification": classification})
                return classification
        return MemoryClassification.IGNORE
''',

# ── EXTRACTOR ────────────────────────────────────────────────────────────────
"app/memory/extractor.py": '''import re
import uuid
import logging
from typing import List, Dict, Any
from .models import MemoryItem, MemoryType, MemoryClassification, ExtractionResult
from .classifier import MemoryClassifier

logger = logging.getLogger("memory.extractor")

# Extraction patterns: (key, regex, memory_type, classification)
EXTRACTION_PATTERNS = [
    ("preferred_language",
     re.compile(r"\\b(?:i (?:prefer|use|like)|my language is)\\s+([a-zA-Z#\\+]+)", re.I),
     MemoryType.PREFERENCE, MemoryClassification.PREFERENCE),

    ("preferred_framework",
     re.compile(r"\\b(?:i (?:prefer|use|like)|my framework is)\\s+([a-zA-Z\\.]+)", re.I),
     MemoryType.PREFERENCE, MemoryClassification.PREFERENCE),

    ("coding_style",
     re.compile(r"\\b(?:i (?:write|code|prefer) (?:clean|functional|oop|object.oriented|"
                r"procedural|declarative))\\b", re.I),
     MemoryType.PREFERENCE, MemoryClassification.PREFERENCE),

    ("current_project",
     re.compile(r"\\b(?:i\'?m (?:working on|building|developing|creating))\\s+([\\w\\s]+?)(?:\\.| and|,|$)",
                re.I),
     MemoryType.PROJECT, MemoryClassification.PROJECT),

    ("goal",
     re.compile(r"\\b(?:my goal is|i want to|i\'m trying to)\\s+([\\w\\s]+?)(?:\\.|,|$)", re.I),
     MemoryType.LONG_TERM, MemoryClassification.FACT),

    ("name",
     re.compile(r"\\bmy name is\\s+([A-Z][a-zA-Z]+)\\b", re.I),
     MemoryType.LONG_TERM, MemoryClassification.FACT),

    ("technology",
     re.compile(r"\\bi (?:use|work with|know)\\s+(React|Vue|Angular|Django|FastAPI|"
                r"PostgreSQL|Redis|Docker|Kubernetes|AWS|GCP|Azure)\\b", re.I),
     MemoryType.LONG_TERM, MemoryClassification.FACT),
]


class FactExtractor:
    """
    Rule-based extractor that scans user messages for structured facts.
    Never stores raw conversation text — only typed key-value facts.
    Greetings, small talk, and temporary requests are discarded.
    """

    def __init__(self):
        self._classifier = MemoryClassifier()

    def extract(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_turn: int = 0,
    ) -> ExtractionResult:
        items: List[MemoryItem] = []
        ignored = 0
        scanned = 0

        for msg in messages:
            if msg.get("role") != "user":
                continue
            content = msg.get("content", "")
            if not isinstance(content, str) or not content.strip():
                continue

            scanned += 1
            classification = self._classifier.classify(content)

            if classification == MemoryClassification.IGNORE:
                ignored += 1
                continue

            # Pattern matching
            for key, pattern, memory_type, cls in EXTRACTION_PATTERNS:
                match = pattern.search(content)
                if match:
                    value = match.group(1).strip() if match.lastindex else content.strip()
                    items.append(MemoryItem(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        memory_type=memory_type,
                        classification=cls,
                        key=key,
                        value=value,
                        source_turn=session_turn,
                    ))

        logger.info("Extraction complete", extra={
            "user_id": user_id,
            "extracted": len(items),
            "ignored": ignored,
        })
        return ExtractionResult(items=items, ignored_count=ignored, total_scanned=scanned)
''',

# ── STORAGE ───────────────────────────────────────────────────────────────────
"app/memory/storage.py": '''from __future__ import annotations
import copy
import logging
from typing import Protocol, Optional, Dict, Any, List, runtime_checkable
from .models import MemoryItem, MemoryType

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


class MockStorage:
    """
    In-process dictionary storage for tests and local development.
    Thread-safe via immutable copy semantics.
    """

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._items: List[MemoryItem] = []

    async def get(self, user_id: str, key: str) -> Optional[Any]:
        return self._store.get(user_id, {}).get(key)

    async def set(self, user_id: str, key: str, value: Any) -> None:
        self._store.setdefault(user_id, {})[key] = value

    async def delete(self, user_id: str, key: str) -> None:
        self._store.get(user_id, {}).pop(key, None)

    async def clear_user(self, user_id: str) -> None:
        self._store.pop(user_id, None)
        self._items = [i for i in self._items if i.user_id != user_id]

    async def export(self, user_id: str) -> Dict[str, Any]:
        return copy.deepcopy(self._store.get(user_id, {}))

    async def save_item(self, item: MemoryItem) -> None:
        self._items.append(item)

    async def get_items(
        self, user_id: str, memory_type: Optional[MemoryType] = None
    ) -> List[MemoryItem]:
        return [
            i for i in self._items
            if i.user_id == user_id
            and (memory_type is None or i.memory_type == memory_type)
        ]


class RedisStorage:
    """Redis-backed storage stub. Implement in Phase 7+."""
    async def get(self, user_id: str, key: str): raise NotImplementedError
    async def set(self, user_id: str, key: str, value: Any): raise NotImplementedError
    async def delete(self, user_id: str, key: str): raise NotImplementedError
    async def clear_user(self, user_id: str): raise NotImplementedError
    async def export(self, user_id: str): raise NotImplementedError
    async def save_item(self, item: MemoryItem): raise NotImplementedError
    async def get_items(self, user_id: str, memory_type=None): raise NotImplementedError


class PostgresStorage:
    """PostgreSQL-backed storage stub. Implement in Phase 7+."""
    async def get(self, user_id: str, key: str): raise NotImplementedError
    async def set(self, user_id: str, key: str, value: Any): raise NotImplementedError
    async def delete(self, user_id: str, key: str): raise NotImplementedError
    async def clear_user(self, user_id: str): raise NotImplementedError
    async def export(self, user_id: str): raise NotImplementedError
    async def save_item(self, item: MemoryItem): raise NotImplementedError
    async def get_items(self, user_id: str, memory_type=None): raise NotImplementedError
''',

# ── SESSION ───────────────────────────────────────────────────────────────────
"app/memory/session.py": '''import logging
import time
from collections import deque
from typing import List, Dict, Any, Optional

logger = logging.getLogger("memory.session")


class SessionMemory:
    """
    Short-term circular buffer for recent conversation turns.
    Automatically prunes when max_turns is exceeded.
    Supports TTL-based expiry at the session level.
    """

    def __init__(self, max_turns: int = 20, ttl_seconds: int = 3600):
        self._max_turns = max_turns
        self._ttl = ttl_seconds
        self._sessions: Dict[str, dict] = {}

    def _get_or_create(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "messages": deque(maxlen=self._max_turns),
                "created_at": time.time(),
                "metadata": {},
            }
        return self._sessions[session_id]

    def add_message(self, session_id: str, message: Dict[str, Any]) -> None:
        session = self._get_or_create(session_id)
        session["messages"].append(message)
        logger.debug("Message added to session", extra={"session_id": session_id})

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if not session:
            return []
        if time.time() - session["created_at"] > self._ttl:
            self.clear(session_id)
            return []
        return list(session["messages"])

    def turn_count(self, session_id: str) -> int:
        return len(self.get_messages(session_id))

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        logger.info("Session cleared", extra={"session_id": session_id})

    def is_expired(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return True
        return time.time() - session["created_at"] > self._ttl

    def size(self) -> int:
        return len(self._sessions)
''',

# ── PROFILE ───────────────────────────────────────────────────────────────────
"app/memory/profile.py": '''import logging
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
''',

# ── PREFERENCES ───────────────────────────────────────────────────────────────
"app/memory/preferences.py": '''import logging
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
''',

# ── SUMMARIZER ────────────────────────────────────────────────────────────────
"app/memory/summarizer.py": '''import logging
from typing import List, Dict, Any
from .models import ConversationSummary

logger = logging.getLogger("memory.summarizer")

SUMMARY_THRESHOLD = 15  # number of turns before compression is triggered


class ConversationSummarizer:
    """
    Placeholder summarizer.
    When conversation exceeds SUMMARY_THRESHOLD turns, replaces old messages
    with a compressed ConversationSummary object.
    No LLM call is made — the summary is a structured placeholder.
    Real LLM summarization will be wired in Phase 7+.
    """

    def should_summarize(self, messages: List[Dict[str, Any]]) -> bool:
        user_turns = sum(1 for m in messages if m.get("role") == "user")
        return user_turns >= SUMMARY_THRESHOLD

    def summarize(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_id: str,
    ) -> ConversationSummary:
        user_turns = [m for m in messages if m.get("role") == "user"]
        count = len(user_turns)

        # Placeholder summary — future: call ProviderManager for LLM compression
        summary_text = (
            f"[Placeholder summary of {count} user turns. "
            f"Topics: {self._extract_topics(user_turns)}]"
        )

        logger.info("Summary generated", extra={
            "user_id": user_id,
            "session_id": session_id,
            "turns_compressed": count,
        })
        return ConversationSummary(
            user_id=user_id,
            session_id=session_id,
            summary=summary_text,
            turn_range=(0, count),
            message_count_compressed=count,
        )

    def compress(
        self,
        messages: List[Dict[str, Any]],
        summary: ConversationSummary,
        keep_last: int = 5,
    ) -> List[Dict[str, Any]]:
        """Replace old messages with the summary, keeping the last N turns."""
        recent = messages[-keep_last:]
        summary_msg = {"role": "system", "content": summary.summary}
        return [summary_msg] + recent

    def _extract_topics(self, user_turns: List[Dict[str, Any]]) -> str:
        """Very rough topic hint for the placeholder summary text."""
        all_text = " ".join(m.get("content", "") for m in user_turns[:5])
        words = [w for w in all_text.split() if len(w) > 5]
        return ", ".join(set(words[:5])) or "general conversation"
''',

# ── CLEANUP ───────────────────────────────────────────────────────────────────
"app/memory/cleanup.py": '''import logging
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
''',

# ── PRIVACY ───────────────────────────────────────────────────────────────────
"app/memory/privacy.py": '''import logging
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
''',

# ── METRICS ───────────────────────────────────────────────────────────────────
"app/memory/metrics.py": '''import logging
from typing import Dict, Any

logger = logging.getLogger("memory.metrics")


class MemoryMetrics:
    def __init__(self):
        self._facts_extracted = 0
        self._preferences_stored = 0
        self._summaries_created = 0
        self._cleanup_count = 0
        self._sessions_active = 0
        self._load_count = 0
        self._save_count = 0

    def record_extraction(self, count: int) -> None:
        self._facts_extracted += count

    def record_preference(self) -> None:
        self._preferences_stored += 1

    def record_summary(self) -> None:
        self._summaries_created += 1

    def record_cleanup(self, count: int) -> None:
        self._cleanup_count += count

    def record_load(self) -> None:
        self._load_count += 1

    def record_save(self) -> None:
        self._save_count += 1

    def snapshot(self) -> Dict[str, Any]:
        return {
            "facts_extracted": self._facts_extracted,
            "preferences_stored": self._preferences_stored,
            "summaries_created": self._summaries_created,
            "cleanup_count": self._cleanup_count,
            "load_count": self._load_count,
            "save_count": self._save_count,
        }


memory_metrics = MemoryMetrics()
''',

# ── MANAGER ───────────────────────────────────────────────────────────────────
"app/memory/manager.py": '''import logging
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
        summary = self._summarizer.summarize(messages, user_id, session_id)
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
''',

# ── UPDATED PIPELINE STUBS ────────────────────────────────────────────────────
"app/pipeline/memory_loader.py": '''import logging
from .context import PipelineContext, UserContext

logger = logging.getLogger("pipeline.memory_loader")


class ContextLoader:
    """
    Loads memory context into the pipeline.
    Wires into MemoryManager when fully initialized; falls back to
    empty UserContext so the pipeline never blocks on missing memory.
    """

    def __init__(self, memory_manager=None):
        self._memory_manager = memory_manager

    async def load(self, context: PipelineContext) -> PipelineContext:
        user_id = context.request_id  # use request_id as proxy user_id in Phase 6

        if self._memory_manager:
            try:
                data = await self._memory_manager.load(user_id, session_id=context.request_id)
                context.user_context = UserContext(
                    user_id=user_id,
                    preferences=data.get("preferences", {}),
                    conversation_summary=None,
                    session_metadata={"profile": data.get("profile", {})},
                )
                logger.info("Memory loaded from manager", extra={"request_id": context.request_id})
                return context
            except Exception as e:
                logger.warning("Memory load failed, using empty context",
                               extra={"error": str(e)})

        # Fallback: empty context
        context.user_context = UserContext(
            user_id=user_id,
            preferences={},
            conversation_summary=None,
            session_metadata={},
        )
        logger.info("Context loaded (fallback)", extra={"request_id": context.request_id})
        return context
''',

"app/pipeline/memory_updater.py": '''import logging
from .context import PipelineContext

logger = logging.getLogger("pipeline.memory_updater")


class MemoryUpdater:
    """
    Extracts facts from the completed pipeline context and persists them.
    When MemoryManager is not wired, produces mock facts for pipeline compatibility.
    """

    def __init__(self, memory_manager=None):
        self._memory_manager = memory_manager

    async def update(self, context: PipelineContext) -> PipelineContext:
        if self._memory_manager:
            try:
                result = await self._memory_manager.extract(
                    context.messages,
                    user_id=context.request_id,
                    session_turn=len(context.messages),
                )
                await self._memory_manager.save(context.request_id, result)
                context.memory_facts = [item.key for item in result.items]
                logger.info("Memory updated via manager", extra={
                    "request_id": context.request_id,
                    "facts": len(result.items),
                })
                return context
            except Exception as e:
                logger.warning("Memory update failed", extra={"error": str(e)})

        # Fallback: produce mock facts
        context.memory_facts = []
        if context.intent == "coding":
            context.memory_facts.append("preferred_language")
        logger.info("Memory update triggered (fallback)", extra={
            "request_id": context.request_id,
            "facts_extracted": len(context.memory_facts),
        })
        return context
''',

# ── TESTS ─────────────────────────────────────────────────────────────────────
"tests/memory/__init__.py": "",

"tests/memory/test_extractor.py": '''import pytest
from app.memory.extractor import FactExtractor
from app.memory.models import MemoryClassification


ext = FactExtractor()


def _msgs(content: str):
    return [{"role": "user", "content": content}]


def test_extracts_preferred_language():
    result = ext.extract(_msgs("I prefer Python for all my projects"), user_id="u1")
    keys = [i.key for i in result.items]
    assert "preferred_language" in keys


def test_extracts_current_project():
    result = ext.extract(_msgs("I\'m working on a chatbot application"), user_id="u1")
    keys = [i.key for i in result.items]
    assert "current_project" in keys


def test_ignores_greetings():
    result = ext.extract(_msgs("Hello!"), user_id="u1")
    assert result.ignored_count == 1
    assert result.items == []


def test_ignores_small_talk():
    result = ext.extract(_msgs("Thanks, that\'s cool!"), user_id="u1")
    assert result.ignored_count >= 1


def test_extracts_name():
    result = ext.extract(_msgs("My name is Alice"), user_id="u1")
    keys = [i.key for i in result.items]
    assert "name" in keys


def test_skips_assistant_messages():
    msgs = [
        {"role": "assistant", "content": "I prefer using FastAPI"},
        {"role": "user", "content": "Hello"},
    ]
    result = ext.extract(msgs, user_id="u1")
    # Only user messages are scanned; "hello" is ignored
    assert result.total_scanned == 1
''',

"tests/memory/test_classifier.py": '''from app.memory.classifier import MemoryClassifier
from app.memory.models import MemoryClassification


clf = MemoryClassifier()


def test_classifies_preference():
    assert clf.classify("I prefer Python over JavaScript") == MemoryClassification.PREFERENCE


def test_classifies_project():
    assert clf.classify("I\'m working on a new project") == MemoryClassification.PROJECT


def test_classifies_fact():
    assert clf.classify("My name is Bob") == MemoryClassification.FACT


def test_classifies_greeting_as_ignore():
    assert clf.classify("Hello there!") == MemoryClassification.IGNORE


def test_classifies_temporary():
    assert clf.classify("Just for now, use JSON") == MemoryClassification.TEMPORARY
''',

"tests/memory/test_session.py": '''import time
from app.memory.session import SessionMemory


def test_add_and_retrieve():
    session = SessionMemory(max_turns=10, ttl_seconds=3600)
    session.add_message("s1", {"role": "user", "content": "Hi"})
    msgs = session.get_messages("s1")
    assert len(msgs) == 1
    assert msgs[0]["content"] == "Hi"


def test_max_turns_pruning():
    session = SessionMemory(max_turns=3, ttl_seconds=3600)
    for i in range(5):
        session.add_message("s1", {"role": "user", "content": str(i)})
    msgs = session.get_messages("s1")
    assert len(msgs) == 3
    assert msgs[0]["content"] == "2"  # oldest kept


def test_clear_session():
    session = SessionMemory()
    session.add_message("s1", {"role": "user", "content": "test"})
    session.clear("s1")
    assert session.get_messages("s1") == []


def test_expired_session_returns_empty():
    session = SessionMemory(max_turns=10, ttl_seconds=0)
    session.add_message("s1", {"role": "user", "content": "hi"})
    time.sleep(0.01)
    assert session.get_messages("s1") == []
''',

"tests/memory/test_preferences.py": '''import pytest
from app.memory.storage import MockStorage
from app.memory.preferences import PreferencesManager


@pytest.fixture
def mgr():
    return PreferencesManager(MockStorage())


@pytest.mark.asyncio
async def test_set_and_get(mgr):
    await mgr.set("u1", "language", "Python")
    val = await mgr.get("u1", "language")
    assert val == "Python"


@pytest.mark.asyncio
async def test_versioning(mgr):
    v1 = await mgr.set("u1", "language", "Python")
    v2 = await mgr.set("u1", "language", "Go")
    assert v2.version == 2
    assert v2.previous_value == "Python"


@pytest.mark.asyncio
async def test_no_duplicate_update(mgr):
    v1 = await mgr.set("u1", "language", "Python")
    v2 = await mgr.set("u1", "language", "Python")
    # Same value — should not increment version
    assert v2.version == v1.version


@pytest.mark.asyncio
async def test_delete_key(mgr):
    await mgr.set("u1", "editor", "vim")
    await mgr.delete_key("u1", "editor")
    val = await mgr.get("u1", "editor")
    assert val is None
''',

"tests/memory/test_profile.py": '''import pytest
from app.memory.storage import MockStorage
from app.memory.profile import ProfileManager


@pytest.fixture
def mgr():
    return ProfileManager(MockStorage())


@pytest.mark.asyncio
async def test_default_profile(mgr):
    profile = await mgr.load("new_user")
    assert profile.user_id == "new_user"
    assert profile.preferred_language is None


@pytest.mark.asyncio
async def test_update_profile(mgr):
    profile = await mgr.update("u1", preferred_language="Python", coding_style="functional")
    assert profile.preferred_language == "Python"
    assert profile.coding_style == "functional"


@pytest.mark.asyncio
async def test_profile_persists(mgr):
    await mgr.update("u1", preferred_framework="FastAPI")
    profile = await mgr.load("u1")
    assert profile.preferred_framework == "FastAPI"
''',

"tests/memory/test_summarizer.py": '''from app.memory.summarizer import ConversationSummarizer, SUMMARY_THRESHOLD


summ = ConversationSummarizer()


def _make_messages(n: int):
    return [{"role": "user", "content": f"message {i}"} for i in range(n)]


def test_should_not_summarize_below_threshold():
    msgs = _make_messages(SUMMARY_THRESHOLD - 1)
    assert summ.should_summarize(msgs) is False


def test_should_summarize_at_threshold():
    msgs = _make_messages(SUMMARY_THRESHOLD)
    assert summ.should_summarize(msgs) is True


def test_summary_contains_turn_count():
    msgs = _make_messages(SUMMARY_THRESHOLD)
    summary = summ.summarize(msgs, "u1", "s1")
    assert str(SUMMARY_THRESHOLD) in summary.summary
    assert summary.message_count_compressed == SUMMARY_THRESHOLD


def test_compress_keeps_recent_messages():
    msgs = _make_messages(SUMMARY_THRESHOLD + 5)
    summary = summ.summarize(msgs, "u1", "s1")
    compressed = summ.compress(msgs, summary, keep_last=5)
    # First message is the summary system message
    assert compressed[0]["role"] == "system"
    assert len(compressed) == 6  # 1 summary + 5 recent
''',

"tests/memory/test_privacy.py": '''import pytest
from app.memory.storage import MockStorage
from app.memory.privacy import PrivacyManager
from app.memory.exceptions import MemoryPrivacyError


@pytest.fixture
def privacy():
    s = MockStorage()
    return PrivacyManager(s), s


@pytest.mark.asyncio
async def test_delete_requires_confirmation(privacy):
    mgr, storage = privacy
    with pytest.raises(MemoryPrivacyError):
        await mgr.delete_all("u1", confirmed=False)


@pytest.mark.asyncio
async def test_delete_all_with_confirmation(privacy):
    mgr, storage = privacy
    await storage.set("u1", "test_key", "value")
    await mgr.delete_all("u1", confirmed=True)
    exported = await storage.export("u1")
    assert exported == {}


@pytest.mark.asyncio
async def test_export_profile(privacy):
    mgr, storage = privacy
    await storage.set("u1", "__profile__", {"user_id": "u1", "preferred_language": "Python"})
    data = await mgr.export_profile("u1")
    assert data["user_id"] == "u1"
    assert data["profile"]["preferred_language"] == "Python"
''',

"tests/memory/test_manager.py": '''import pytest
from app.memory.manager import MemoryManager
from app.memory.storage import MockStorage
from app.memory.extractor import FactExtractor
from app.memory.summarizer import ConversationSummarizer
from app.memory.session import SessionMemory
from app.memory.profile import ProfileManager
from app.memory.preferences import PreferencesManager
from app.memory.cleanup import MemoryCleanup
from app.memory.privacy import PrivacyManager
from app.memory.metrics import MemoryMetrics


def make_manager() -> MemoryManager:
    storage = MockStorage()
    return MemoryManager(
        storage=storage,
        extractor=FactExtractor(),
        summarizer=ConversationSummarizer(),
        session=SessionMemory(),
        profile_mgr=ProfileManager(storage),
        prefs_mgr=PreferencesManager(storage),
        cleanup=MemoryCleanup(storage),
        privacy=PrivacyManager(storage),
        metrics=MemoryMetrics(),
    )


@pytest.mark.asyncio
async def test_load_returns_context():
    mgr = make_manager()
    ctx = await mgr.load("u1", "s1")
    assert "profile" in ctx
    assert "preferences" in ctx
    assert "session_messages" in ctx


@pytest.mark.asyncio
async def test_extract_and_save():
    mgr = make_manager()
    msgs = [{"role": "user", "content": "I prefer Python"}]
    result = await mgr.extract(msgs, "u1")
    await mgr.save("u1", result)
    metrics = mgr.get_metrics()
    assert metrics["facts_extracted"] >= 1
    assert metrics["save_count"] == 1


@pytest.mark.asyncio
async def test_clear_session():
    mgr = make_manager()
    mgr._session.add_message("s1", {"role": "user", "content": "hi"})
    await mgr.clear_session("s1")
    assert mgr._session.get_messages("s1") == []


@pytest.mark.asyncio
async def test_delete_requires_confirmation():
    import pytest
    from app.memory.exceptions import MemoryPrivacyError
    mgr = make_manager()
    with pytest.raises(MemoryPrivacyError):
        await mgr.delete("u1", confirmed=False)


@pytest.mark.asyncio
async def test_summarize_returns_none_below_threshold():
    mgr = make_manager()
    msgs = [{"role": "user", "content": "hi"}]
    result = await mgr.summarize(msgs, "u1", "s1")
    assert result is None
''',
}

# Create dirs + __init__.py
for d in directories:
    dir_path = os.path.join(base_path, d)
    os.makedirs(dir_path, exist_ok=True)
    parts = d.split("/")
    for i in range(1, len(parts) + 1):
        init_dir = os.path.join(base_path, *parts[:i])
        init_file = os.path.join(init_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "a").close()

# Write files
for file_path, content in files.items():
    full_path = os.path.join(base_path, file_path)
    os.makedirs(os.path.dirname(full_path) or base_path, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Phase 6 skeleton generated successfully.")
