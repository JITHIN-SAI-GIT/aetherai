from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MemoryFact(BaseModel):
    key: str
    value: Any
    confidence: float = 1.0
    source: str = "extracted"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None             # extracted from "my name is X" / "I'm X"
    preferred_language: Optional[str] = None
    preferred_provider: Optional[str] = None
    preferred_framework: Optional[str] = None
    favorite_technologies: List[str] = Field(default_factory=list)
    writing_tone: Optional[str] = None
    coding_style: Optional[str] = None
    current_project: Optional[str] = None
    goals: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PreferenceVersion(BaseModel):
    value: Any
    previous_value: Optional[Any] = None
    version: int = 1
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserPreferences(BaseModel):
    user_id: str
    preferences: Dict[str, PreferenceVersion] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectContext(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True
