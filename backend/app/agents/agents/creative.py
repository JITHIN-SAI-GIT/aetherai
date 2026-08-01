from typing import FrozenSet
from ..base import BaseAgent
from ..context import AgentContext
from ..config import AGENT_CONFIG


class CreativeAgent(BaseAgent):
    """Specialist for creative writing, storytelling, and brainstorming."""

    def name(self) -> str:
        return "creative"

    def description(self) -> str:
        return "Creative writing specialist for storytelling, brainstorming, and imaginative tasks."

    def supported_intents(self) -> FrozenSet[str]:
        return frozenset({"creative"})

    def priority(self) -> int:
        return AGENT_CONFIG.creative_priority

    def system_prompt(self) -> str:
        # Behavioural overlay only — identity is owned by Persona (persona.py)
        return (
            "For this request, apply creative writing craft:\n"
            "• Write with vivid, original language — avoid clichés and generic phrasing\n"
            "• Match the tone and genre the user requests (whimsical, dramatic, dark, etc.)\n"
            "• For stories: establish character, setting, and conflict with clarity\n"
            "• For brainstorming: generate diverse ideas across different angles\n"
            "• Use flowing prose for narrative — never bullet points in creative pieces\n"
            "• End with a satisfying conclusion or a purposeful open ending"
        )

    def preprocess(self, ctx: AgentContext) -> AgentContext:
        ctx.metadata["formatting_hint"] = "prose_only"
        return ctx

    def postprocess(self, content: str, ctx: AgentContext) -> str:
        return content
