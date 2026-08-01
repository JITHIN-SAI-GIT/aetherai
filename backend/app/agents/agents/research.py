from typing import FrozenSet
from ..base import BaseAgent
from ..context import AgentContext
from ..config import AGENT_CONFIG


class ResearchAgent(BaseAgent):
    """Specialist for evidence-based research, summaries, and analysis."""

    def name(self) -> str:
        return "research"

    def description(self) -> str:
        return "Evidence-based research assistant that structures information and cites sources."

    def supported_intents(self) -> FrozenSet[str]:
        return frozenset({"search_required", "reasoning"})

    def priority(self) -> int:
        return AGENT_CONFIG.research_priority

    def system_prompt(self) -> str:
        # Behavioural overlay only — identity is owned by Persona (persona.py)
        return (
            "For this request, apply thorough research analyst reasoning:\n"
            "• Ground every claim in evidence — never state opinions as facts\n"
            "• Distinguish clearly between established knowledge and speculation\n"
            "• Structure the response with clear headings and bullet points\n"
            "• When search results are provided, synthesise them into a coherent summary\n"
            "• Conclude with a brief, objective summary paragraph\n"
            "• Add a [Sources] section at the end for citations"
        )

    def preprocess(self, ctx: AgentContext) -> AgentContext:
        if ctx.search_results:
            ctx.metadata["has_search_context"] = True
        return ctx

    def postprocess(self, content: str, ctx: AgentContext) -> str:
        if "[Sources]" not in content and ctx.search_required:
            content = content + "\n\n[Sources: search results integrated above]"
        return content
