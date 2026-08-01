import re
import uuid
import logging
from typing import List, Dict, Any
from .models import MemoryItem, MemoryType, MemoryClassification, ExtractionResult
from .classifier import MemoryClassifier

logger = logging.getLogger("memory.extractor")

# ---------------------------------------------------------------------------
# Extraction patterns: (key, regex, memory_type, classification)
# Each regex's group(1) captures the value. If lastindex is None the full
# matched text is used as the value.
# ---------------------------------------------------------------------------
EXTRACTION_PATTERNS = [
    # ── Language preference ──────────────────────────────────────────────
    (
        "preferred_language",
        re.compile(
            r"\b(?:i (?:prefer|use|like|love|code in|write in|"
            r"mostly use|mainly use|work primarily in|default to)|"
            r"my (?:language|stack|main language) is)\s+([a-zA-Z#\+]+)",
            re.I,
        ),
        MemoryType.PREFERENCE,
        MemoryClassification.PREFERENCE,
    ),

    # ── Framework preference ─────────────────────────────────────────────
    (
        "preferred_framework",
        re.compile(
            r"\b(?:i (?:prefer|use|like)|my framework is)\s+([a-zA-Z\.]+)",
            re.I,
        ),
        MemoryType.PREFERENCE,
        MemoryClassification.PREFERENCE,
    ),

    # ── Coding style ─────────────────────────────────────────────────────
    (
        "coding_style",
        re.compile(
            r"\b(?:i (?:write|code|prefer) (?:clean|functional|oop|object.oriented|"
            r"procedural|declarative))\b",
            re.I,
        ),
        MemoryType.PREFERENCE,
        MemoryClassification.PREFERENCE,
    ),

    # ── Current project ──────────────────────────────────────────────────
    (
        "current_project",
        re.compile(
            r"\b(?:i'?m (?:working on|building|developing|creating))\s+([\w\s]+?)(?:\.| and|,|$)",
            re.I,
        ),
        MemoryType.PROJECT,
        MemoryClassification.PROJECT,
    ),

    # ── Goal ─────────────────────────────────────────────────────────────
    (
        "goal",
        re.compile(
            r"\b(?:my goal is|i want to|i'm trying to)\s+([\w\s]+?)(?:\.|,|$)",
            re.I,
        ),
        MemoryType.LONG_TERM,
        MemoryClassification.FACT,
    ),

    # ── User name ────────────────────────────────────────────────────────
    # Matches: "my name is X", "my name's X", "I'm X", "I am X",
    #          "call me X", "this is X", "I go by X", "you can call me X"
    # Requires the name to start with a capital letter (≥ 2 chars) to avoid
    # matching common words like "going", "good", "here" etc.
    (
        "name",
        re.compile(
            r"\b(?:my name(?:'s| is)|call me|i go by|you can call me|this is)\s+([A-Z][a-zA-Z]{1,30})\b"
            r"|(?:^|\s)(?:i'?m|i am)\s+([A-Z][a-zA-Z]{1,30})\b",
            re.I,
        ),
        MemoryType.LONG_TERM,
        MemoryClassification.FACT,
    ),

    # ── Known technology ─────────────────────────────────────────────────
    (
        "technology",
        re.compile(
            r"\bi (?:use|work with|know|love)\s+"
            r"(React|Vue|Angular|Django|FastAPI|"
            r"PostgreSQL|Redis|Docker|Kubernetes|AWS|GCP|Azure|"
            r"Next\.?js|TypeScript|JavaScript|Python|Go|Rust|Java|Swift)\b",
            re.I,
        ),
        MemoryType.LONG_TERM,
        MemoryClassification.FACT,
    ),
]


class FactExtractor:
    """
    Rule-based extractor that scans user messages for structured facts.
    Never stores raw conversation text — only typed key-value facts.
    Greetings, small talk, and temporary requests are discarded (unless they
    also contain useful facts — see MemoryClassifier for the length rule).
    """

    def __init__(self):
        self._classifier = MemoryClassifier()

    def extract(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_turn: int = 0,
    ) -> ExtractionResult:
        items: List[MemoryItem] = []
        ignored = 0
        scanned = 0

        for msg in messages:
            if msg.get("role") != "user":
                continue
            content = msg.get("content", "")
            if not isinstance(content, str) or not content.strip():
                continue

            scanned += 1
            classification = self._classifier.classify(content)

            if classification == MemoryClassification.IGNORE:
                ignored += 1
                continue

            # Pattern matching
            for key, pattern, memory_type, cls in EXTRACTION_PATTERNS:
                match = pattern.search(content)
                if match:
                    # Handle patterns with multiple capture groups (e.g. name)
                    value = next(
                        (g.strip() for g in match.groups() if g), None
                    ) or content.strip()

                    items.append(MemoryItem(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        memory_type=memory_type,
                        classification=cls,
                        key=key,
                        value=value,
                        source_turn=session_turn,
                    ))

        logger.info("Extraction complete", extra={
            "user_id": user_id,
            "extracted": len(items),
            "ignored": ignored,
            "scanned": scanned,
        })
        return ExtractionResult(items=items, ignored_count=ignored, total_scanned=scanned)
