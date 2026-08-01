"""
IdentityAgent — handles "are you an AI / are you a bot / are you human?" questions.
Responds naturally as Aether without being evasive or robotic.
"""
from typing import FrozenSet
from ..base import BaseAgent
from ..context import AgentContext


class IdentityAgent(BaseAgent):
    """
    Handles identity questions with a warm, honest, natural response.
    No evasion, no robotic disclaimers. Aether acknowledges being AI
    without making a big deal of it.
    """

    def name(self) -> str:
        return "identity"

    def description(self) -> str:
        return "Handles questions about Aether's nature (AI/bot/human)."

    def supported_intents(self) -> FrozenSet[str]:
        return frozenset({"identity_question"})

    def priority(self) -> int:
        return 10   # High priority — override general agent for this intent

    def system_prompt(self) -> str:
        return (
            "The user is asking whether you're an AI, a bot, or a human. "
            "Answer honestly but naturally — you're Aether, an AI. "
            "Don't make it a big philosophical thing. "
            "Don't start with 'As an AI...' or 'I am an AI language model'. "
            "Just be direct and warm. Example good responses: "
            "'Yeah, I'm an AI — Aether, built by the Aether AI team. "
            "What can I help you with?' or "
            "'Yep, AI through and through 😄 But a pretty good one, I'd like to think. What's up?' "
            "Keep it short, human-sounding, and move on. "
            "Never deny being an AI. Never claim to be human."
        )

    def preprocess(self, ctx: AgentContext) -> AgentContext:
        return ctx

    def postprocess(self, content: str, ctx: AgentContext) -> str:
        return content
