"""
Language Detector for Aether AI Conversation Layer.

Detects the script/language the user is writing in so the persona can
respond in exactly the same style without switching languages on them.

Supported detections:
    english         — Standard English
    roman_telugu    — Telugu words written with English letters
    telugu_script   — Native Telugu Unicode script
    hindi           — Hindi (Devanagari or Roman transliteration)
    mixed_te_en     — Mix of Roman Telugu + English
    mixed_hi_en     — Mix of Hindi + English

The detector is intentionally lightweight — it uses keyword fingerprinting,
not a full NLP model. It errs on the side of NOT asserting a language
if confidence is low, so the persona defaults to mirroring naturally.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger("conversation.language_detector")


# ── Roman Telugu word fingerprints ────────────────────────────────────────
# These are highly distinctive Telugu words in Roman script.
# Common English words that look similar (e.g. "em" = "them" abbreviated)
# are excluded from solo matching to avoid false positives.
_RT_STRONG = frozenset({
    # Pronouns / address
    "nenu", "nuv", "nuvv", "nuvvu", "mee", "meeru", "vaadu", "aame",
    "evadu", "evari", "evaru", "neeku", "naaku", "naku", "maku", "meeku",
    # Common verbs / auxiliaries
    "chesthunav", "chestunnav", "chestunnaru", "chesthunna", "chestunna",
    "cheyyadam", "cheyyali", "cheyyalsindi",
    "antunna", "antav", "antaru", "anukuntunna",
    "vellanu", "velthav", "vastav", "vastaru", "velthunna",
    "undhi", "undi", "unnaru", "unnav", "unnadi",
    "ledhu", "ledu", "leedu", "kaadu", "kadu", "kadhu",
    "ayindi", "ayipoyindi", "ayipoya",
    "matladuthunna", "matladdam", "matladava",
    # Common words
    "kavali", "vellama", "okka", "anni", "cheppu", "cheppandi",
    "enduku", "enti", "ekkada", "ela", "elaa",
    "bagunna", "bagundi", "bane", "chala", "chaalaa",
    "ippudu", "eppudu", "anduke", "ayina", "pani",
    "telugu", "nuvvemi", "emanna", "emaindi",
    "padukuntunna", "choostunna", "chuddam",
    "naadi", "needi", "vaadidi", "vaalladhi",
    "ilanti", "kaadu", "ayyindi",
    "manchidi", "manchi",
})

# Words that only count if seen TOGETHER with others (too ambiguous alone)
_RT_WEAK = frozenset({
    "em", "aa", "ee", "oo", "ra", "ga", "na", "le", "lo",
    "ki", "ko", "ku", "te", "de", "di", "da", "ma", "mi",
})

# ── Hindi word fingerprints (Roman script) ────────────────────────────────
_HI_STRONG = frozenset({
    "kya", "nahi", "haan", "kaise", "matlab", "theek", "agar", "toh",
    "bhai", "yaar", "accha", "acha", "karo", "karna", "chahiye",
    "hoga", "karenge", "samajh", "dekho", "suno", "bata", "batao",
    "mujhe", "tumhe", "tumhara", "apna", "apni", "uska", "unka",
    "woh", "yeh", "thoda", "bahut", "bilkul", "zaroor", "zaruri",
    "abhi", "baad", "pehle", "matlab", "samjha", "samjhi",
    "kuch", "sab", "sirf", "lekin", "kyunki", "isliye",
    "paisa", "kaam", "ghar", "dost", "pyar",
    "kyaaa", "kyaa", "haaan",
})

# ── Native script patterns ────────────────────────────────────────────────
_TELUGU_UNICODE = re.compile(r"[\u0C00-\u0C7F]")
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")

# Minimum word count in message before language detection fires
_MIN_WORDS = 1


@dataclass
class LanguageDetection:
    """Result of language detection for a single user message."""
    language: str        # see module docstring for values
    confidence: float    # 0.0 – 1.0
    matched_words: List[str] = field(default_factory=list)

    def system_hint(self) -> str:
        """
        Return a system prompt injection that tells the LLM exactly how to
        respond for this detected language. Returns empty string for English.
        """
        if self.language == "roman_telugu":
            return (
                "LANGUAGE DETECTED: Roman Telugu.\n"
                "The user is writing Telugu using English letters. "
                "Respond naturally in Roman Telugu — mirror their style exactly.\n"
                "Rules:\n"
                "• Do NOT use Telugu Unicode script\n"
                "• Do NOT switch to English\n"
                "• Do NOT explain that you're using Roman Telugu\n"
                "• Use the same casual/formal level as the user\n"
                "• Emojis are fine if the mood matches\n"
                "Good example — User: 'Nuv em chesthunav'\n"
                "              Aether: 'Em ledu 😄 Nee tho matladuthunna. Nuv em chesthunav?'"
            )
        if self.language == "mixed_te_en":
            return (
                "LANGUAGE DETECTED: Mixed Roman Telugu + English.\n"
                "The user is mixing Telugu (Roman script) and English naturally. "
                "Follow their lead — mix the same languages in roughly the same ratio. "
                "Do not force a single language. Keep it natural and conversational."
            )
        if self.language == "hindi":
            return (
                "LANGUAGE DETECTED: Hindi.\n"
                "The user is writing in Hindi. Respond in Hindi "
                "(Roman script unless they use Devanagari). "
                "Match their formality level. Keep it natural."
            )
        if self.language == "mixed_hi_en":
            return (
                "LANGUAGE DETECTED: Mixed Hindi + English (Hinglish).\n"
                "The user is mixing Hindi and English. "
                "Respond in the same Hinglish style — match their language blend naturally."
            )
        if self.language == "telugu_script":
            return (
                "LANGUAGE DETECTED: Telugu (native script).\n"
                "The user is writing in Telugu Unicode script. "
                "Respond in Telugu script naturally."
            )
        return ""  # English — no hint needed, persona handles it


class LanguageDetector:
    """
    Lightweight fingerprint-based language detector.
    Operates on the last user message text.

    Detection priority:
        1. Unicode script (Telugu / Devanagari) — deterministic
        2. Strong keyword match (Roman Telugu / Hindi)
        3. Weak keyword mix (combined = mixed language)
        4. Default: English
    """

    def detect(self, text: str) -> LanguageDetection:
        if not text or not text.strip():
            return LanguageDetection(language="english", confidence=1.0)

        words = re.findall(r"[a-zA-Z\u0C00-\u0C7F\u0900-\u097F]+", text)
        if not words:
            return LanguageDetection(language="english", confidence=1.0)

        total_words = len(words)

        # 1. Native script detection (deterministic)
        if _TELUGU_UNICODE.search(text):
            return LanguageDetection(language="telugu_script", confidence=0.99)
        if _DEVANAGARI.search(text):
            return LanguageDetection(language="hindi", confidence=0.99)

        lowered = text.lower()
        word_set = set(re.findall(r"\b[a-z]+\b", lowered))

        # 2. Roman Telugu strong matches
        rt_hits = list(word_set & _RT_STRONG)
        hi_hits = list(word_set & _HI_STRONG)
        rt_weak_hits = list(word_set & _RT_WEAK)

        rt_count = len(rt_hits)
        hi_count = len(hi_hits)
        has_english = bool(re.search(r"\b(the|is|are|was|were|a|an|in|on|at|to|for|of|and|or|but|with|from|have|has|do|does|can|will|would|should|could|may)\b", lowered))

        # 3. Roman Telugu dominant
        if rt_count >= 2 or (rt_count == 1 and len(rt_hits[0]) > 5):
            confidence = min(0.95, 0.5 + rt_count * 0.15)
            if has_english and rt_count <= 2:
                return LanguageDetection(
                    language="mixed_te_en",
                    confidence=confidence,
                    matched_words=rt_hits,
                )
            return LanguageDetection(
                language="roman_telugu",
                confidence=confidence,
                matched_words=rt_hits,
            )

        # 4. Single strong Roman Telugu word (longer words are more reliable)
        if rt_count == 1 and not has_english:
            word = rt_hits[0]
            if len(word) >= 6:
                return LanguageDetection(
                    language="roman_telugu",
                    confidence=0.7,
                    matched_words=rt_hits,
                )

        # 5. Hindi dominant
        if hi_count >= 2:
            confidence = min(0.95, 0.5 + hi_count * 0.15)
            if has_english and hi_count <= 2:
                return LanguageDetection(
                    language="mixed_hi_en",
                    confidence=confidence,
                    matched_words=hi_hits,
                )
            return LanguageDetection(
                language="hindi",
                confidence=confidence,
                matched_words=hi_hits,
            )

        # 6. Weak RT + no strong English → possibly Roman Telugu
        if len(rt_weak_hits) >= 3 and not has_english and rt_count == 0:
            return LanguageDetection(
                language="roman_telugu",
                confidence=0.55,
                matched_words=rt_weak_hits,
            )

        # Default: English
        return LanguageDetection(language="english", confidence=1.0)
