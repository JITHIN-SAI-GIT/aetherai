import re
import logging
from typing import Dict, List
from .context import PipelineContext

logger = logging.getLogger("pipeline.intent")

# Intent keyword registry – easy to extend by adding new entries
INTENT_RULES: Dict[str, List[str]] = {
    "coding":               ["code", "function", "class", "bug", "debug", "python", "javascript",
                             "implement", "algorithm", "script", "syntax", "compiler",
                             # Roman Telugu coding keywords
                             "code cheyyali", "code kavali", "coding help", "code cheyyadam",
                             # Hindi coding keywords
                             "code karna", "code karo", "program banana"],
    "reasoning":            ["why", "explain", "reason", "because", "cause", "logic", "analyze",
                             "argument", "inference", "deduce",
                             "enduku", "ela", "explain cheyyi"],
    "math":                 ["calculate", "solve", "equation", "integral", "derivative", "proof",
                             "formula", "algebra", "geometry", "matrix", "sum"],
    "creative":             ["write", "story", "poem", "imagine", "creative", "fiction", "rhyme",
                             "narrative", "compose",
                             "story rayu", "poem rayu", "rayyali"],
    "translation":          ["translate", "in french", "in spanish", "in german", "language",
                             "convert to", "in japanese", "lo cheppu", "lo translate",
                             "telugu lo", "english lo", "hindi lo"],
    "search_required":      ["latest", "current", "today", "news", "2024", "2025", "2026",
                             "recent", "now", "live", "real-time", "breaking", "trending",
                             "weather", "forecast", "temperature", "rain",
                             "score", "standings", "points table", "ipl", "who won",
                             "price", "stock", "version", "release", "new",
                             "this week", "this month", "this year",
                             "update", "announced", "launched", "released", "what happened",
                             # Multilingual equivalents
                             "ippatiki", "ippudu", "recent ga"],
    "clarification_required": ["what do you mean", "clarify", "not clear", "elaborate", "rephrase",
                             "artham kaledu", "samajh nahi aaya"],
    "tool_request":         ["call", "use tool", "function call", "execute", "run", "invoke"],
    "identity_question":    ["are you an ai", "are you a bot", "are you human", "are you real",
                             "who are you", "what are you", "are you chatgpt", "are you gpt",
                             "are you a robot", "are you sentient", "do you have feelings",
                             "are you alive", "are you a person",
                             # Multilingual variants
                             "nuvvu ai va", "nuvvu bot va", "nuvvu manishi va",
                             "kya tum ai ho", "kya tum bot ho"],
    "chat":                 ["hi", "hello", "hey", "hii", "helo",
                             "nuv em", "em chesthunav", "ela unnav", "ela undi",
                             "kya haal", "kaise ho", "kya chal"],
}


class IntentDetector:
    """
    Rule-based intent classification strategy.
    Scans the last user message for keyword patterns.
    Defaults to 'chat'. Easy to replace with an ML strategy later.
    """

    def detect(self, context: PipelineContext) -> PipelineContext:
        last_user_message = self._get_last_user_message(context.messages)
        intent = self._classify(last_user_message)
        context.intent = intent

        logger.info(
            "Intent detected",
            extra={
                "request_id": context.request_id,
                "intent": intent,
            }
        )
        return context

    # ── Private helpers ──────────────────────────────────────────────────────

    def _get_last_user_message(self, messages: List[Dict]) -> str:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                return content if isinstance(content, str) else ""
        return ""

    def _classify(self, text: str) -> str:
        lowered = text.lower()
        for intent, keywords in INTENT_RULES.items():
            if any(re.search(r'\b' + re.escape(kw) + r'\b', lowered) for kw in keywords):
                return intent
        return "chat"
