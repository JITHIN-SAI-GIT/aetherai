import re
import logging
from typing import List, Optional
from .models import QualityResult, StyleResult
from .policies import POLICIES

logger = logging.getLogger("conversation.quality")

# ── Pattern-level AI filler detection ────────────────────────────────────────
# These patterns catch structural AI markers that n-gram detection misses.
# They match even when varied slightly (e.g. "I completely understand").
_AI_FILLER_PATTERNS = [
    # Opener patterns (first 60 chars of response)
    re.compile(r"^(Sure[,!]?\s|Of course[,!]?\s|Certainly[,!]?\s|Absolutely[,!]?\s)", re.I),
    re.compile(r"^(No problem[,!]?\s|Happy to\s|Glad to\s|I'd be happy)", re.I),
    re.compile(r"^(I understand\b|I see\b|I completely\b)", re.I),
    re.compile(r"^(Great[,!]\s|Excellent[,!]\s|Wonderful[,!]\s|Perfect[,!]\s)", re.I),
    # Closer patterns (last 100 chars of response)
    re.compile(r"(I hope (this|that) helps\.?\s*$)", re.I),
    re.compile(r"(Feel free to (ask|reach out)\.?\s*$)", re.I),
    re.compile(r"(Let me know if you (need|have|want).*$)", re.I),
    re.compile(r"(Don't hesitate to (ask|contact).*$)", re.I),
    re.compile(r"(Is there anything else.*\??\s*$)", re.I),
]

# ── Repeated sentence-opener detection ───────────────────────────────────────
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_OPENER_WORDS = 2   # compare first N words of each sentence


def _extract_opener(sentence: str) -> Optional[str]:
    """Return the first _OPENER_WORDS lowercased words of a sentence."""
    words = sentence.strip().split()
    if len(words) < 2:
        return None
    return " ".join(w.lower() for w in words[:_OPENER_WORDS])


class QualityReviewer:
    """
    Validates every response before it reaches the user.
    Checks:
        1. Empty / too short / too long
        2. Banned exact phrases (from POLICIES)
        3. AI filler pattern detection (opener/closer regex)
        4. Repeated sentence openers (structural pattern repetition)
        5. N-gram repetition (sliding window)
    Issues are corrected where possible, otherwise flagged for logging.
    """

    def review(self, content: str, style: StyleResult) -> QualityResult:
        issues: List[str] = []
        corrected = content
        corrections = 0

        # ── 1. Empty response ──────────────────────────────────────────────
        if not content or not content.strip():
            issues.append("response is empty")
            corrected = "Hmm, something went wrong — mind rephrasing that? 🙏"
            corrections += 1
            return QualityResult(
                passed=False, issues=issues,
                corrected_content=corrected, corrections_applied=corrections,
            )

        # ── 2. Length bounds ───────────────────────────────────────────────
        if len(content.strip()) < POLICIES.min_response_length:
            issues.append(f"response too short ({len(content.strip())} chars)")

        if len(content.strip()) > POLICIES.max_response_length:
            corrected = content[:POLICIES.max_response_length] + "\n\n[Truncated for length]"
            issues.append("response too verbose — truncated")
            corrections += 1

        # ── 3. Banned exact phrases ────────────────────────────────────────
        active = corrected or content
        for phrase in POLICIES.banned_phrases:
            if phrase.lower() in active.lower():
                # Case-insensitive removal preserving surrounding whitespace
                pattern = re.compile(re.escape(phrase), re.I)
                active = pattern.sub("", active).strip()
                issues.append(f"banned phrase removed: {phrase!r}")
                corrections += 1
        corrected = active

        # ── 4. AI filler pattern detection ───────────────────────────────
        stripped = corrected.strip()
        opener_60 = stripped[:60]
        closer_100 = stripped[-100:] if len(stripped) > 100 else stripped

        for pat in _AI_FILLER_PATTERNS:
            if pat.search(opener_60) or pat.search(closer_100):
                issues.append(f"AI filler pattern detected: {pat.pattern!r}")
                # Flag only — structural rewrites left to the LLM in next turn
                break

        # ── 5. Repeated sentence openers ─────────────────────────────────
        repeated_opener = self._find_repeated_opener(corrected)
        if repeated_opener:
            issues.append(f"repeated sentence opener: {repeated_opener!r}")

        # ── 6. N-gram repetition ──────────────────────────────────────────
        repeated_ngram = self._find_repetition(corrected)
        if repeated_ngram:
            issues.append(f"repeated n-gram: {repeated_ngram!r}")

        passed = len(issues) == 0
        logger.info("Quality review complete", extra={
            "passed": passed,
            "issues_count": len(issues),
            "corrections": corrections,
        })
        return QualityResult(
            passed=passed,
            issues=issues,
            corrected_content=corrected if corrections else None,
            corrections_applied=corrections,
        )

    # ── Private helpers ────────────────────────────────────────────────────

    def _find_repetition(self, text: str, n: int = 4) -> str:
        """Detect repeated n-grams within a sliding window."""
        words = text.lower().split()
        seen: set = set()
        for i in range(len(words) - n + 1):
            gram = tuple(words[i: i + n])
            if gram in seen:
                return " ".join(gram)
            seen.add(gram)
        return ""

    def _find_repeated_opener(self, text: str) -> str:
        """
        Detect structural repetition: multiple sentences starting with the
        same word pair (e.g. 'I will... I will... I will...').
        Only flags if 3+ sentences share the same opener.
        """
        sentences = _SENTENCE_SPLIT.split(text)
        if len(sentences) < 3:
            return ""
        openers: List[str] = []
        for s in sentences:
            op = _extract_opener(s)
            if op:
                openers.append(op)
        # Check if any opener appears 3+ times
        from collections import Counter
        counts = Counter(openers)
        for opener, count in counts.items():
            if count >= 3:
                return opener
        return ""
