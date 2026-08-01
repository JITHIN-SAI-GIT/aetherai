import re
import logging
from .models import MemoryClassification

logger = logging.getLogger("memory.classifier")

# Pattern → classification mapping (evaluated in order)
CLASSIFICATION_RULES = [
    # Greetings and pure small talk (length check is applied separately — see classify())
    (re.compile(r"^(hi|hello|hey|thanks|thank you|ok|okay|sure|great|cool|bye)\b", re.I),
     MemoryClassification.IGNORE),

    # Temporary / transient (must come before preference to avoid false matches)
    (re.compile(r"\b(today|right now|currently|for now|just this once|temporary)\b", re.I),
     MemoryClassification.TEMPORARY),

    # Projects
    (re.compile(r"\b(project|building|working on|developing|creating)\b", re.I),
     MemoryClassification.PROJECT),

    # Preferences (explicit)
    (re.compile(
        r"\b(prefer|like|love|use|favorite|always use|usually|tend to use|"
        r"my style|my preference|i want|i need)\b", re.I),
     MemoryClassification.PREFERENCE),

    # Facts (declarative knowledge)
    (re.compile(
        r"\b(my name is|i am|i work|my goal|i'm a|i specialize|"
        r"i know|my background|i have experience|call me|i go by)\b", re.I),
     MemoryClassification.FACT),
]

# Short message threshold: messages at or below this word count that start
# with a greeting pattern are considered pure greetings and ignored.
_GREETING_IGNORE_MAX_WORDS = 7


class MemoryClassifier:
    """
    Assigns a MemoryClassification to a raw text snippet.
    Rule-based; designed to be replaced with an ML classifier in future phases.

    Key fix: greeting patterns only trigger IGNORE for short messages (≤ 7 words).
    A message like "Hi! My name is Jithin and I prefer Python" starts with a
    greeting but is long — it contains valuable facts and must be processed.
    """

    def classify(self, text: str) -> MemoryClassification:
        word_count = len(text.split())
        for pattern, classification in CLASSIFICATION_RULES:
            if pattern.search(text):
                # Only IGNORE pure/short greetings — long messages may contain facts
                if (classification == MemoryClassification.IGNORE
                        and word_count > _GREETING_IGNORE_MAX_WORDS):
                    logger.debug(
                        "Greeting pattern matched but message is long — continuing scan",
                        extra={"text_len": len(text), "word_count": word_count},
                    )
                    continue  # keep scanning the remaining rules
                logger.debug(
                    "Classified",
                    extra={"text_len": len(text), "classification": classification},
                )
                return classification
        return MemoryClassification.IGNORE
