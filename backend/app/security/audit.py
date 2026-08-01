import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("security.audit")


@dataclass
class AuditEvent:
    event_type: str          # injection | jailbreak | rate_limit | content | validation | auth | abuse
    reason: str
    ip: Optional[str] = None
    user_id: Optional[str] = None
    api_key_prefix: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    """
    Records every security event in a structured, privacy-safe log.
    NEVER logs user message contents — only event type, reason, and identity hints.
    """

    def __init__(self, max_events: int = 1000):
        self._events: List[AuditEvent] = []
        self._max_events = max_events

    def record(
        self,
        event_type: str,
        reason: str,
        ip: Optional[str] = None,
        user_id: Optional[str] = None,
        api_key_prefix: Optional[str] = None,
        **metadata,
    ) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            reason=reason,
            ip=ip,
            user_id=user_id,
            api_key_prefix=api_key_prefix,
            metadata=metadata,
        )
        # Circular buffer — evict oldest when full
        if len(self._events) >= self._max_events:
            self._events.pop(0)
        self._events.append(event)

        logger.warning(
            "Security event",
            extra={
                "event_type": event_type,
                "reason": reason,
                "ip": ip,
                "user_id": user_id,
            },
        )
        return event

    def recent(self, n: int = 50) -> List[Dict[str, Any]]:
        events = self._events[-n:]
        return [
            {
                "event_type": e.event_type,
                "reason": e.reason,
                "ip": e.ip,
                "user_id": e.user_id,
                "timestamp": e.timestamp,
                "metadata": e.metadata,
            }
            for e in reversed(events)
        ]

    def count(self) -> int:
        return len(self._events)


audit_logger = AuditLogger()
