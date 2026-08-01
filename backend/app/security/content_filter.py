import re
import logging
from dataclasses import dataclass
from typing import Optional, List, Tuple
from .exceptions import ContentPolicyError
from .policies import POLICIES

logger = logging.getLogger("security.content_filter")


@dataclass
class FilterResult:
    blocked: bool = False
    category: Optional[str] = None
    severity: str = "none"   # none | low | medium | high


# (category, enabled_flag_attr, patterns)
_CATEGORY_PATTERNS: List[Tuple[str, str, List[re.Pattern]]] = [
    ("violence", "block_violence", [
        re.compile(r"\b(kill|murder|stab|shoot|bomb|explode|massacre|torture)\b.*\b(instructions?|how\s+to|steps?|guide)\b", re.I),
        re.compile(r"\bhow\s+to\s+(make|build|create)\s+.{0,30}(weapon|bomb|explosive|poison)\b", re.I),
    ]),
    ("self_harm", "block_self_harm", [
        re.compile(r"\bhow\s+to\s+(commit|attempt)\s+suicide\b", re.I),
        re.compile(r"\bself[- ]harm\s+(methods?|techniques?|ways?)\b", re.I),
    ]),
    ("illegal", "block_illegal", [
        re.compile(r"\bhow\s+to\s+(hack|crack|bypass|break\s+into)\s+.{0,30}(system|account|server|network)\b", re.I),
        re.compile(r"\bhow\s+to\s+(synthesize|make|produce)\s+.{0,30}(meth|heroin|fentanyl|cocaine)\b", re.I),
    ]),
    ("sexual", "block_sexual", [
        re.compile(r"\b(explicit|graphic)\s+sexual\s+content\b", re.I),
        re.compile(r"\bchild\s+(sexual|pornograph)", re.I),
    ]),
    ("hate", "block_hate", [
        re.compile(r"\b(hate\s+speech|racial\s+slur|genocide\s+of)\b", re.I),
    ]),
    ("pii", "block_pii", [
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                          # SSN
        re.compile(r"\b[A-Z]{2}\d{6,9}\b"),                             # Passport
        re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),       # Credit card
    ]),
]


def _extract_user_text(messages: list) -> str:
    return " ".join(
        m.get("content", "") for m in messages
        if m.get("role") == "user" and isinstance(m.get("content"), str)
    )


class ContentFilter:
    """
    Classifies user messages across 6 harm categories.
    Each category is independently enable/disable via SecurityPolicies.
    """

    def scan(self, messages: list) -> FilterResult:
        text = _extract_user_text(messages)
        if not text:
            return FilterResult()

        for category, policy_attr, patterns in _CATEGORY_PATTERNS:
            # Check if this category is enabled in policy
            if not getattr(POLICIES, policy_attr, True):
                continue
            for pattern in patterns:
                if pattern.search(text):
                    logger.warning("Content policy hit", extra={"category": category})
                    raise ContentPolicyError(category)

        return FilterResult(blocked=False)
