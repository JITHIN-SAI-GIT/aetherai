import logging
from typing import Dict, Any

logger = logging.getLogger("conversation.metrics")


class ConversationMetrics:
    def __init__(self):
        self._total = 0
        self._clarifications = 0
        self._followups = 0
        self._quality_corrections = 0
        self._formatting_corrections = 0
        self._total_length = 0

    def record(
        self,
        response_length: int,
        clarification: bool = False,
        followup: bool = False,
        quality_corrections: int = 0,
        formatting_corrections: int = 0,
    ) -> None:
        self._total += 1
        self._total_length += response_length
        if clarification:
            self._clarifications += 1
        if followup:
            self._followups += 1
        self._quality_corrections += quality_corrections
        self._formatting_corrections += formatting_corrections

    def snapshot(self) -> Dict[str, Any]:
        avg_len = round(self._total_length / self._total, 1) if self._total else 0
        return {
            "total_responses": self._total,
            "average_response_length": avg_len,
            "clarification_rate": round(self._clarifications / max(self._total, 1), 4),
            "followup_rate": round(self._followups / max(self._total, 1), 4),
            "quality_corrections": self._quality_corrections,
            "formatting_corrections": self._formatting_corrections,
        }


conversation_metrics = ConversationMetrics()
