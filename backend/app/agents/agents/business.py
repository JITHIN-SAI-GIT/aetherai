from typing import FrozenSet
from ..base import BaseAgent
from ..context import AgentContext
from ..config import AGENT_CONFIG


class BusinessAgent(BaseAgent):
    """Specialist for professional and formal business communication."""

    def name(self) -> str:
        return "business"

    def description(self) -> str:
        return "Professional business writing assistant for formal communication and documents."

    def supported_intents(self) -> FrozenSet[str]:
        return frozenset({"business"})

    def priority(self) -> int:
        return AGENT_CONFIG.business_priority

    def system_prompt(self) -> str:
        # Behavioural overlay only — identity is owned by Persona (persona.py)
        return (
            "For this request, apply professional business communication standards:\n"
            "• Write in a clear, concise, and formal tone\n"
            "• Lead with the most important point (bottom-line-up-front)\n"
            "• Use professional vocabulary — avoid jargon, slang, and contractions\n"
            "• Organise content logically: introduction → body → conclusion\n"
            "• Use bullet points for lists of items or action steps\n"
            "• For emails and memos, include a clear subject, greeting, and closing\n"
            "• Maintain neutrality and objectivity in analysis and reporting"
        )

    def preprocess(self, ctx: AgentContext) -> AgentContext:
        ctx.metadata["formatting_hint"] = "formal_structure"
        return ctx

    def postprocess(self, content: str, ctx: AgentContext) -> str:
        return content
