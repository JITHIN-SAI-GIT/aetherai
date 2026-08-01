import logging
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
