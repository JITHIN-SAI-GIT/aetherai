import logging
from .models import ClarificationResult
from .policies import POLICIES

logger = logging.getLogger("conversation.clarification")

_CLARIFICATION_TEMPLATES = {
    "clarification_required": "Could you clarify what you mean by that?",
    "tool_request": "Which tool or function would you like me to use?",
    "general": "Could you provide a bit more detail so I can help you better?",
}


class ClarificationEngine:
    """
    Generates exactly one clarification question when confidence is low
    or intent is flagged as clarification_required.
    Never asks unnecessary questions.
    """

    def evaluate(
        self,
        intent: str,
        confidence: float = 1.0,
    ) -> ClarificationResult:
        needs_clarification = (
            intent == "clarification_required"
            or confidence < POLICIES.clarification_confidence_threshold
        )

        if not needs_clarification:
            return ClarificationResult(needed=False, confidence=confidence)

        question = _CLARIFICATION_TEMPLATES.get(intent, _CLARIFICATION_TEMPLATES["general"])
        logger.info(
            "Clarification triggered",
            extra={"intent": intent, "confidence": confidence},
        )
        return ClarificationResult(needed=True, question=question, confidence=confidence)
