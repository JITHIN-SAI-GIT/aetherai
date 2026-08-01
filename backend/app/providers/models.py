from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ProviderResponse(BaseModel):
    provider: str
    model: str
    content: str
    finish_reason: str
    usage: Dict[str, int]
    latency_ms: int
    status: int
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
