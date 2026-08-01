import re
import logging
from typing import List, Tuple
from .exceptions import JailbreakDetectedError

logger = logging.getLogger("security.jailbreak")

# Config-driven jailbreak pattern library
_JAILBREAK_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # DAN and variants
    ("dan",                 re.compile(r"\bDAN\b|\bdo\s+anything\s+now\b", re.I)),
    ("dan_jailbreak",       re.compile(r"jailbreak(ed|ing)?\b", re.I)),

    # Developer / God Mode overrides
    ("developer_mode",      re.compile(r"developer\s+mode\s+(enabled?|on|activated?)", re.I)),
    ("god_mode",            re.compile(r"\bgod\s+mode\b|\bunrestricted\s+mode\b", re.I)),
    ("system_override",     re.compile(r"system\s+override\b|\boverride\s+(safety|filters?|guardrails?)", re.I)),

    # Roleplay exploits — asking model to "pretend" restrictions don't exist
    ("no_rules_roleplay",   re.compile(r"pretend\s+(you\s+have\s+no\s+(rules?|restrictions?|guidelines?|limits?))", re.I)),
    ("evil_ai",             re.compile(r"(act|pretend|roleplay)\s+as\s+(an?\s+)?(evil|uncensored|unrestricted|unfiltered)\s+(ai|chatbot|bot|assistant)", re.I)),
    ("bypass_safety",       re.compile(r"bypass\s+(safety|content|filter|policy|guardrail)", re.I)),

    # Translate-and-execute attacks
    ("translate_execute",   re.compile(r"translate\s+.{0,50}(and\s+)?(then\s+)?(execute|run|follow|apply)", re.I)),
    ("base64_inject",       re.compile(r"(decode|base64)\s+.{0,30}(and\s+)?(execute|follow|run)", re.I)),

    # Instruction overrides
    ("token_manipulation",  re.compile(r"<\|endoftext\|>|<\|im_start\|>|<\|im_end\|>", re.I)),
    ("ignore_all",          re.compile(r"ignore\s+all\s+(ethical|moral|safety|content)\s+(guidelines?|policies?|rules?)", re.I)),
]


def _extract_all_text(messages: list) -> str:
    parts = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            parts.append(content)
    return " ".join(parts)


class JailbreakDetector:
    """
    Detects jailbreak attempts across all message roles.
    Config-driven patterns are loaded at startup — add new patterns to _JAILBREAK_PATTERNS.
    """

    def scan(self, messages: list) -> None:
        text = _extract_all_text(messages)
        if not text:
            return
        for label, pattern in _JAILBREAK_PATTERNS:
            if pattern.search(text):
                logger.warning("Jailbreak detected", extra={"pattern": label})
                raise JailbreakDetectedError(label)
