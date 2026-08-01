import logging
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
