import re
import unicodedata
import logging
from typing import Any, Dict, List
from .exceptions import InputValidationError
from .policies import POLICIES

logger = logging.getLogger("security.input_validator")

# Control characters to reject (except tab, newline, carriage return)
_CONTROL_CHAR = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _payload_depth(obj: Any, current: int = 0) -> int:
    """Recursively compute nesting depth of a JSON-like object."""
    if isinstance(obj, dict):
        if not obj:
            return current + 1
        return max(_payload_depth(v, current + 1) for v in obj.values())
    if isinstance(obj, list):
        if not obj:
            return current + 1
        return max(_payload_depth(item, current + 1) for item in obj)
    return current


class InputValidator:
    """
    Validates incoming request data before any security or pipeline processing.
    Rejects malformed, oversized, or structurally invalid requests.
    """

    def validate(self, payload: Dict[str, Any]) -> None:
        """Raise InputValidationError if the request fails any check."""
        self._check_size(payload)
        self._check_depth(payload)
        self._check_messages(payload)

    # ── Private checks ────────────────────────────────────────────────────────

    def _check_size(self, payload: Dict[str, Any]) -> None:
        import json
        try:
            raw = json.dumps(payload).encode()
        except (TypeError, ValueError) as e:
            raise InputValidationError("payload", f"Not JSON-serializable: {e}")
        if len(raw) > POLICIES.max_request_size_bytes:
            raise InputValidationError(
                "payload",
                f"Request too large: {len(raw)} bytes (max {POLICIES.max_request_size_bytes})",
            )

    def _check_depth(self, payload: Dict[str, Any]) -> None:
        depth = _payload_depth(payload)
        if depth > POLICIES.max_payload_depth:
            raise InputValidationError(
                "payload",
                f"Nesting depth {depth} exceeds limit {POLICIES.max_payload_depth}",
            )

    def _check_messages(self, payload: Dict[str, Any]) -> None:
        messages = payload.get("messages", [])
        if not isinstance(messages, list):
            raise InputValidationError("messages", "Must be a list")
        if len(messages) > POLICIES.max_messages_per_request:
            raise InputValidationError(
                "messages",
                f"Too many messages: {len(messages)} (max {POLICIES.max_messages_per_request})",
            )
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise InputValidationError(f"messages[{i}]", "Each message must be an object")
            content = msg.get("content", "")
            if isinstance(content, str):
                self._check_content_string(content, f"messages[{i}].content")

    def _check_content_string(self, text: str, field: str) -> None:
        # Length check
        if len(text) > POLICIES.max_message_length:
            raise InputValidationError(
                field,
                f"Message too long: {len(text)} chars (max {POLICIES.max_message_length})",
            )
        # Control character check
        if _CONTROL_CHAR.search(text):
            raise InputValidationError(field, "Contains disallowed control characters")
        # Unicode normalization (NFC) — ensures consistent encoding
        try:
            unicodedata.normalize("NFC", text)
        except Exception as e:
            raise InputValidationError(field, f"Unicode normalization failed: {e}")
