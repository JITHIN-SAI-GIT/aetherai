import time
import logging
from typing import Dict, Tuple
from .exceptions import AbuseDetectedError
from .policies import POLICIES

logger = logging.getLogger("security.abuse_detector")


class AbuseDetector:
    """
    Tracks security violations per IP address.
    When a threshold is crossed, applies a configurable temporary ban.
    All tracking is in-process; persistent bans require Redis (Phase 9+).
    """

    def __init__(self):
        # ip -> (violation_count, ban_expires_at)
        self._records: Dict[str, Tuple[int, float]] = {}

    def record_violation(self, ip: str) -> None:
        """Record a security violation for an IP. Raises AbuseDetectedError if banned."""
        now = time.time()
        count, ban_until = self._records.get(ip, (0, 0.0))

        # Check if currently banned
        if ban_until > now:
            remaining = ban_until - now
            logger.warning("Banned IP attempted request",
                           extra={"ip": ip, "ban_remaining": remaining})
            raise AbuseDetectedError(ip, remaining)

        # Increment violation counter
        count += 1
        self._records[ip] = (count, ban_until)

        if count >= POLICIES.abuse_violation_threshold:
            ban_expires = now + POLICIES.abuse_ban_seconds
            self._records[ip] = (count, ban_expires)
            logger.warning("IP temporarily banned",
                           extra={"ip": ip, "ban_seconds": POLICIES.abuse_ban_seconds})
            raise AbuseDetectedError(ip, POLICIES.abuse_ban_seconds)

    def is_banned(self, ip: str) -> bool:
        count, ban_until = self._records.get(ip, (0, 0.0))
        return ban_until > time.time()

    def violation_count(self, ip: str) -> int:
        return self._records.get(ip, (0, 0.0))[0]

    def reset(self, ip: str) -> None:
        self._records.pop(ip, None)
