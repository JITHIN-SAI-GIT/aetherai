import os
from dataclasses import dataclass, field
from typing import FrozenSet


@dataclass(frozen=True)
class SecurityPolicies:
    """
    Immutable security configuration loaded from environment variables.
    All thresholds and limits are configurable without code changes.
    """
    # Input limits
    max_message_length: int = int(os.getenv("SEC_MAX_MSG_LEN", "8000"))
    max_messages_per_request: int = int(os.getenv("SEC_MAX_MSGS", "50"))
    max_payload_depth: int = int(os.getenv("SEC_MAX_DEPTH", "5"))
    max_request_size_bytes: int = int(os.getenv("SEC_MAX_REQUEST_BYTES", "524288"))  # 512KB

    # Rate limiting (sliding window)
    rate_limit_ip_per_minute: int = int(os.getenv("SEC_RATE_IP_PM", "60"))
    rate_limit_user_per_minute: int = int(os.getenv("SEC_RATE_USER_PM", "120"))
    rate_limit_key_per_minute: int = int(os.getenv("SEC_RATE_KEY_PM", "300"))
    rate_burst_multiplier: float = float(os.getenv("SEC_BURST_MULT", "2.0"))

    # Abuse detection
    abuse_violation_threshold: int = int(os.getenv("SEC_ABUSE_THRESH", "10"))
    abuse_ban_seconds: float = float(os.getenv("SEC_BAN_SECS", "300.0"))

    # Content policy (True = enabled)
    block_violence: bool = os.getenv("SEC_BLOCK_VIOLENCE", "true").lower() == "true"
    block_self_harm: bool = os.getenv("SEC_BLOCK_SELFHARM", "true").lower() == "true"
    block_illegal: bool = os.getenv("SEC_BLOCK_ILLEGAL", "true").lower() == "true"
    block_sexual: bool = os.getenv("SEC_BLOCK_SEXUAL", "true").lower() == "true"
    block_hate: bool = os.getenv("SEC_BLOCK_HATE", "true").lower() == "true"
    block_pii: bool = os.getenv("SEC_BLOCK_PII", "false").lower() == "true"

    # Secret filter
    entropy_threshold: float = float(os.getenv("SEC_ENTROPY_THRESH", "4.5"))
    min_entropy_string_len: int = int(os.getenv("SEC_ENTROPY_MIN_LEN", "20"))

    # API key auth
    api_key_header: str = os.getenv("SEC_API_KEY_HEADER", "Authorization")
    api_keys_enabled: bool = os.getenv("SEC_API_KEYS_ENABLED", "false").lower() == "true"


POLICIES = SecurityPolicies()
