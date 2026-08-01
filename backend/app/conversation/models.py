from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ToneResult(BaseModel):
    tone: str
    system_hint: str
    source: str = "auto"  # "user_preference" | "intent" | "default"


class StyleResult(BaseModel):
    style: str
    formatting_hints: List[str] = Field(default_factory=list)
    code_expected: bool = False
    use_markdown: bool = True


class QualityResult(BaseModel):
    passed: bool = True
    issues: List[str] = Field(default_factory=list)
    corrected_content: Optional[str] = None
    corrections_applied: int = 0


class FollowUpResult(BaseModel):
    needed: bool = False
    question: Optional[str] = None
    reason: Optional[str] = None


class ClarificationResult(BaseModel):
    needed: bool = False
    question: Optional[str] = None
    confidence: float = 1.0


class ConversationContext(BaseModel):
    tone: ToneResult
    style: StyleResult
    persona_instructions: str
    clarification: ClarificationResult
    follow_up: FollowUpResult
    enriched_content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
