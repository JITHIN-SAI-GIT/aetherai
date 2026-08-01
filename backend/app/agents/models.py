from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class AgentSelection(BaseModel):
    """Result of the router's decision — which agent won and why."""
    agent_name: str
    confidence: float = 1.0
    reason: str = ""
    is_fallback: bool = False


class AgentResult(BaseModel):
    """What the selected agent contributes to the pipeline context."""
    agent_name: str
    system_prompt: str
    preprocessing_notes: List[str] = Field(default_factory=list)
    postprocessed_content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
