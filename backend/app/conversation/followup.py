import logging
import random
from typing import List, Dict, Any, Optional
from .models import FollowUpResult

logger = logging.getLogger("conversation.followup")

# Intents that might genuinely need clarification
_FOLLOWUP_INTENTS = {"coding", "creative", "research"}

# Ambiguity signals — vague references in short messages
_AMBIGUITY_SIGNALS = [
    "something", "stuff", "thing", "it", "this", "that",
    "maybe", "perhaps", "not sure", "kind of",
]

# ── Context-aware follow-up questions ─────────────────────────────────────────
# Grouped by intent. Randomly selected to avoid repetitive phrasing.
_FOLLOWUP_BY_INTENT: Dict[str, List[str]] = {
    "coding": [
        "Which language / framework are you working with?",
        "Can you share what you've tried so far?",
        "What's the error message you're seeing?",
        "Python, JS, or something else?",
        "What's the expected behaviour vs what's actually happening?",
        "nuv em language use chesthunav?",   # Roman Telugu variant
    ],
    "creative": [
        "What tone are you going for — funny, serious, romantic, dark?",
        "Any specific characters or setting in mind?",
        "How long should it be?",
        "Who's the target audience?",
    ],
    "research": [
        "Any specific angle you want me to focus on?",
        "How deep do you want this — summary or full analysis?",
        "Any particular sources or time period to prioritise?",
    ],
    "chat": [
        "Tell me more?",
        "Interesting — go on.",
    ],
}

# Generic fallback questions — used ONLY when intent-specific ones don't apply
_GENERIC_FOLLOWUP = [
    "Can you share a bit more context?",
    "What exactly are you trying to do?",
    "More details would help — what's the goal?",
]

# Roman Telugu ambiguity signals
_RT_AMBIGUITY_SIGNALS = [
    "enti", "em", "emi", "adi", "ee", "aa", "oka", "okati",
]


class FollowUpEngine:
    """
    Determines whether a follow-up question should be asked and,
    if so, what to ask.

    Rules:
    - Only fires for intents that genuinely need clarification (coding, creative, research)
    - Only fires for short/ambiguous messages (< 5 words or contains vague references)
    - Questions are intent-specific and randomly selected to avoid repetition
    - Never asks 'Could you share more details?' — uses natural variants instead
    - Detects Roman Telugu ambiguity signals so follow-up isn't stuck in English
    """

    def evaluate(
        self,
        messages: List[Dict[str, Any]],
        intent: str,
        response_content: str = "",
        detected_language: str = "english",
    ) -> FollowUpResult:
        last_user_msg = self._last_user_message(messages)

        # ── Short message in a clarification-worthy intent ─────────────────
        if intent in _FOLLOWUP_INTENTS and len(last_user_msg.split()) < 5:
            question = self._pick_question(intent, detected_language)
            return FollowUpResult(
                needed=True,
                question=question,
                reason="user message too short for intent",
            )

        # ── Ambiguity signal detection ─────────────────────────────────────
        lower = last_user_msg.lower()
        for signal in _AMBIGUITY_SIGNALS:
            if f" {signal} " in f" {lower} " and len(last_user_msg.split()) < 10:
                question = self._pick_question(intent, detected_language)
                return FollowUpResult(
                    needed=True,
                    question=question,
                    reason=f"ambiguity signal: '{signal}'",
                )

        # ── Roman Telugu ambiguity signals ──────────────────────────────────
        if detected_language in ("roman_telugu", "mixed_te_en"):
            for signal in _RT_AMBIGUITY_SIGNALS:
                if f" {signal} " in f" {lower} " and len(last_user_msg.split()) < 8:
                    # Pick a Roman Telugu or generic follow-up
                    question = self._pick_question(intent, detected_language)
                    return FollowUpResult(
                        needed=True,
                        question=question,
                        reason=f"RT ambiguity signal: '{signal}'",
                    )

        return FollowUpResult(needed=False)

    # ── Private helpers ────────────────────────────────────────────────────

    def _pick_question(self, intent: str, detected_language: str = "english") -> str:
        """
        Select a context-aware follow-up question.
        For Roman Telugu users, prefer Telugu variants when available.
        """
        candidates = _FOLLOWUP_BY_INTENT.get(intent, _GENERIC_FOLLOWUP)

        # If Roman Telugu user, prefer any Telugu-variant questions
        if detected_language in ("roman_telugu", "mixed_te_en"):
            telugu_qs = [q for q in candidates if any(
                c in q for c in ["nuv", "kavali", "em ", "ela ", "cheyyi", "cheppu"]
            )]
            if telugu_qs:
                return random.choice(telugu_qs)

        return random.choice(candidates)

    def _last_user_message(self, messages: List[Dict[str, Any]]) -> str:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                return content if isinstance(content, str) else ""
        return ""
