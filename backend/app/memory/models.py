from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MemoryType(str, Enum):
    SHORT_TERM  = "short_term"
    LONG_TERM   = "long_term"
    SESSION     = "session"
    PROFILE     = "profile"
    PREFERENCE  = "preference"
    SUMMARY     = "summary"
    PROJECT     = "project"


class MemoryClassification(str, Enum):
    PREFERENCE  = "preference"
    FACT        = "fact"
    PROJECT     = "project"
    TEMPORARY   = "temporary"
    IGNORE      = "ignore"


class MemoryItem(BaseModel):
    id: str
    user_id: str
    memory_type: MemoryType
    classification: MemoryClassification
    key: str
    value: Any
    confidence: float = 1.0
    source_turn: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    items: List[MemoryItem] = Field(default_factory=list)
    ignored_count: int = 0
    total_scanned: int = 0


class ConversationSummary(BaseModel):
    user_id: str
    session_id: str
    summary: str
    turn_range: tuple
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message_count_compressed: int = 0
