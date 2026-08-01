from dataclasses import dataclass


@dataclass(frozen=True)
class ConversationPolicies:
    """Immutable global conversation rules. Config-driven in Phase 8+."""
    min_response_length: int = 10
    max_response_length: int = 4000
    clarification_confidence_threshold: float = 0.6
    max_repetition_phrase_len: int = 5
    repetition_window: int = 50        # words to scan for repeated n-grams
    keep_last_n_messages: int = 10
    banned_phrases: tuple = (
        # ── AI self-identification ────────────────────────────────────────
        "As an AI language model",
        "As a large language model",
        "I'm just an AI",
        "As an artificial intelligence",
        "I cannot assist with",
        "I am unable to",
        "I don't have personal opinions",
        "I don't have feelings",
        "I am an AI",
        # ── Hollow openers — the clearest robot markers ───────────────────
        "Great question!",
        "That's a great question",
        "That's a good question",
        "What a great question",
        "Excellent question",
        "Certainly!",
        "Of course!",
        "Absolutely!",
        "Sure thing",
        "By all means",
        "I'd be happy to",
        "I'd be glad to",
        "I would be happy to",
        "I would be glad to",
        "I can help with that",
        "I can certainly help",
        "I am here to help",
        # ── Filler acknowledgements ───────────────────────────────────────
        "I understand your concern",
        "I understand where you're coming from",
        "I completely understand",
        "I understand",
        "I see what you mean",
        "That makes sense",
        # ── Filler endings ────────────────────────────────────────────────
        "I hope this helps",
        "I hope that helps",
        "I hope this answers your question",
        "Feel free to ask",
        "Feel free to reach out",
        "Let me know if you need anything else",
        "Don't hesitate to ask",
        "Is there anything else I can help",
        "Is there anything else you'd like",
        "Let me know if you have any questions",
        "If you have any more questions",
        # ── Empty affirmations ────────────────────────────────────────────
        "That's a great point",
        "That's a good point",
        "As requested",
        "As you mentioned",
    )
    # Patterns that should NEVER open a response (case-insensitive prefix check)
    banned_openers: tuple = (
        "I understand",
        "I see",
        "Sure",
        "Certainly",
        "Of course",
        "Absolutely",
        "Great",
        "Excellent",
        "Wonderful",
        "Of course",
        "No problem",
        "Happy to",
        "Glad to",
    )
    default_tone: str = "friendly"   # was "professional" — caused robotic casual responses
    default_style: str = "general"


# Module-level singleton
POLICIES = ConversationPolicies()
