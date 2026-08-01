from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class AgentContext:
    """
    Read-only input DTO passed to agents during preprocess/postprocess.
    Agents must not mutate the pipeline context directly.
    All agent decisions flow back through AgentResult.
    """
    intent: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    user_profile: Dict[str, Any] = field(default_factory=dict)
    search_required: bool = False
    search_results: List[str] = field(default_factory=list)
    conversation_summary: Optional[str] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def last_user_message(self) -> str:
        """Convenience accessor — returns the most recent user message content."""
        for msg in reversed(self.messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                return content if isinstance(content, str) else ""
        return ""
