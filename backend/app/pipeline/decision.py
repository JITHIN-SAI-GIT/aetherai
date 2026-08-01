from dataclasses import dataclass


@dataclass
class IntentDecision:
    """Carries the result of intent detection for logging purposes."""
    intent: str
    confidence: float = 1.0
    source: str = "rule_based"
