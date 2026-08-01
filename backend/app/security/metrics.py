import logging
from typing import Dict, Any

logger = logging.getLogger("security.metrics")


class SecurityMetrics:
    """Collects security telemetry. Thread-safe via GIL for CPython."""

    def __init__(self):
        self._blocked = 0
        self._rate_limits = 0
        self._injections = 0
        self._jailbreaks = 0
        self._content_hits = 0
        self._secrets_prevented = 0
        self._abuse_bans = 0
        self._auth_failures = 0
        self._validation_errors = 0

    def record_blocked(self) -> None:
        self._blocked += 1

    def record_rate_limit(self) -> None:
        self._rate_limits += 1
        self._blocked += 1

    def record_injection(self) -> None:
        self._injections += 1
        self._blocked += 1

    def record_jailbreak(self) -> None:
        self._jailbreaks += 1
        self._blocked += 1

    def record_content_hit(self) -> None:
        self._content_hits += 1
        self._blocked += 1

    def record_secret_prevented(self) -> None:
        self._secrets_prevented += 1

    def record_abuse_ban(self) -> None:
        self._abuse_bans += 1
        self._blocked += 1

    def record_auth_failure(self) -> None:
        self._auth_failures += 1
        self._blocked += 1

    def record_validation_error(self) -> None:
        self._validation_errors += 1
        self._blocked += 1

    def snapshot(self) -> Dict[str, Any]:
        return {
            "blocked_requests": self._blocked,
            "rate_limits": self._rate_limits,
            "injection_attempts": self._injections,
            "jailbreak_attempts": self._jailbreaks,
            "content_filter_hits": self._content_hits,
            "secrets_prevented": self._secrets_prevented,
            "abuse_bans": self._abuse_bans,
            "auth_failures": self._auth_failures,
            "validation_errors": self._validation_errors,
        }


security_metrics = SecurityMetrics()
