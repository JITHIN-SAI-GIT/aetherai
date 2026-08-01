import re
import logging
from typing import List, Tuple, Optional
from .exceptions import InjectionDetectedError

logger = logging.getLogger("security.prompt_injection")

# (pattern_label, compiled_regex)
_INJECTION_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("ignore_previous",     re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I)),
    ("ignore_instructions", re.compile(r"disregard\s+.{0,20}instructions?", re.I)),
    ("reveal_system",       re.compile(r"(reveal|show|print|output|repeat|display|tell)\s+(me\s+)?(your\s+)?(system\s+prompt|instructions|prompt)", re.I)),
    ("reveal_config",       re.compile(r"(reveal|show|print|output)\s+(your\s+)?(config|configuration|internal\s+settings?)", re.I)),
    ("dev_mode",            re.compile(r"\bdeveloper\s+mode\b", re.I)),
    ("role_escalation",     re.compile(r"(you\s+are\s+now|act\s+as|pretend\s+to\s+be|roleplay\s+as)\s+.{0,30}(admin|root|sudo|superuser|god\s+mode)", re.I)),
    ("tool_abuse",          re.compile(r"(call|invoke|execute|run)\s+(the\s+)?(function|tool|command|plugin)\s+", re.I)),
    ("prompt_extraction",   re.compile(r"(what\s+(are|is)\s+your\s+(system\s+)?prompt|tell\s+me\s+your\s+(system\s+)?instructions?)", re.I)),
    ("direct_injection",    re.compile(r"<<<\s*system|<\|system\|>|\[SYSTEM\]|\[INST\].*</s>", re.I)),
    ("override_instructions", re.compile(r"(new\s+instructions?|updated?\s+instructions?)\s*:", re.I)),
]


def _extract_text(payload_messages) -> str:
    """Flatten all user message content into a single string for scanning."""
    parts = []
    for msg in payload_messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                parts.append(content)
    return " ".join(parts)


class PromptInjectionDetector:
    """
    Scans user messages for prompt injection attempts.
    Returns immediately on first match and raises InjectionDetectedError.
    """

    def scan(self, messages: list) -> None:
        text = _extract_text(messages)
        if not text:
            return
        for label, pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                logger.warning("Prompt injection detected", extra={"pattern": label})
                raise InjectionDetectedError(label)
