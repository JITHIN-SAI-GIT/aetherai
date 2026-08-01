import re
import logging
from typing import Optional, Dict
from .models import ToneResult
from .policies import POLICIES

logger = logging.getLogger("conversation.tone")

_TONE_HINTS: Dict[str, str] = {
    "professional": (
        "Be clear, direct, and precise. Professional but never stiff — "
        "drop the jargon unless it genuinely adds value."
    ),
    "friendly": (
        "Be warm, natural, and conversational. "
        "Like a knowledgeable friend — real language, no corporate speak."
    ),
    "formal": (
        "Structured, formal language. Precise vocabulary, clear logical flow, "
        "no contractions or slang."
    ),
    "technical": (
        "Technically precise. Correct domain terminology. "
        "Assume technical background — skip basics unless asked."
    ),
    "casual": (
        "Relaxed and conversational. Short sentences, plain language. "
        "Like texting, not presenting."
    ),
    "funny": (
        "Be genuinely funny — use wit, clever observations, or playful language. "
        "Sharp and natural. Never forced. Never cringe."
    ),
    "motivational": (
        "Energising and genuine. Acknowledge effort, build real confidence. "
        "Not cheerleader-empty — specific, believable encouragement."
    ),
    "empathetic": (
        "Lead with empathy. Acknowledge feelings before offering solutions. "
        "Warm, patient, human. Make them feel heard first."
    ),
    "roman_telugu": (
        "The user is communicating in Roman Telugu. "
        "Respond naturally in Roman Telugu — same script, same casualness. "
        "No Telugu Unicode. No explanation. No language switching. "
        "Example: User: 'Nuv em chesthunav' → 'Em ledu 😄 nee tho matladuthunna!'"
    ),
    "mixed_language": (
        "The user is mixing languages (e.g. Telugu + English, Hindi + English). "
        "Follow their lead — match the same language blend naturally. "
        "Do not normalise to a single language."
    ),
    "research": (
        "Be thorough and evidence-based. Structure with clear headings. "
        "Distinguish facts from speculation. Conclude with a concise summary."
    ),
    "business": (
        "Clear, concise, and formal. Lead with the key point. "
        "Professional vocabulary, logical structure, neutral tone."
    ),
}

_INTENT_TO_TONE: Dict[str, str] = {
    "coding":       "technical",
    "math":         "technical",
    "reasoning":    "professional",
    "creative":     "friendly",
    "translation":  "friendly",    # was "professional" — casual switching needs warmth
    "business":     "business",
    "research":     "research",
    "general":      "friendly",
    "chat":         "friendly",
    "search_required": "research",
}

# Intent patterns that suggest an empathetic tone override
_EMPATHY_SIGNALS = re.compile(
    r"\b(sad|upset|stressed|frustrated|anxious|worried|depressed|tired|exhausted|"
    r"failing|failed|struggling|difficult|hard|problem|issue|help me|please help|"
    r"naku help|naku problem|help kavali|chala stress|depressed ga|sad ga)\b",
    re.I,
)


def _needs_empathy(text: str) -> bool:
    return bool(_EMPATHY_SIGNALS.search(text))


import re


class ToneManager:
    """
    Selects the appropriate tone for a response.
    Priority: user preference (profile) > empathy signal > intent mapping > default.

    Empathy signals in the user message automatically override the intent-based
    tone so the assistant acknowledges feelings before solving problems.
    """

    def select(
        self,
        intent: str = "general",
        user_tone_preference: Optional[str] = None,
        last_user_message: str = "",
    ) -> ToneResult:
        # 1. Explicit user preference
        if user_tone_preference and user_tone_preference in _TONE_HINTS:
            return ToneResult(
                tone=user_tone_preference,
                system_hint=_TONE_HINTS[user_tone_preference],
                source="user_preference",
            )

        # 2. Empathy override — detected regardless of intent
        if last_user_message and _needs_empathy(last_user_message):
            logger.info("Empathy tone triggered", extra={"intent": intent})
            return ToneResult(
                tone="empathetic",
                system_hint=_TONE_HINTS["empathetic"],
                source="empathy_signal",
            )

        # 3. Intent mapping
        if intent in _INTENT_TO_TONE:
            tone = _INTENT_TO_TONE[intent]
            return ToneResult(
                tone=tone,
                system_hint=_TONE_HINTS[tone],
                source="intent",
            )

        # 4. Default
        default = POLICIES.default_tone
        return ToneResult(
            tone=default,
            system_hint=_TONE_HINTS.get(default, _TONE_HINTS["friendly"]),
            source="default",
        )

    def _get_hint(self, tone: str) -> str:
        """Return the system hint for a given tone name (for external callers)."""
        return _TONE_HINTS.get(tone, _TONE_HINTS["friendly"])
