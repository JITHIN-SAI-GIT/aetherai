from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum


class SearchCategory(str, Enum):
    NEWS = "news"
    WEATHER = "weather"
    SPORTS = "sports"
    GENERAL = "general"


class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str
    source: Optional[str] = None
    published: Optional[str] = None
    summary: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    provider: str
    cache_hit: bool = False
    latency_ms: float = 0.0
    category: SearchCategory = SearchCategory.GENERAL


class SearchDecision(BaseModel):
    required: bool
    reason: str
    confidence: float = 1.0
    category: SearchCategory = SearchCategory.GENERAL


class CacheEntry(BaseModel):
    query_hash: str
    results: List[SearchResult]
    provider: str
    ttl_seconds: int
    category: str
    hits: int = 0
