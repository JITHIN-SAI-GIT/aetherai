from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class RoutingStrategy(str, Enum):
    """
    The knowledge routing decision made by the SearchDetector stage.

    INTERNAL  — answered from the LLM's training knowledge (timeless facts)
    MEMORY    — answered from the user's long-term memory store
    SEARCH    — answered from a live web search
    HYBRID    — search results merged with long-term memory context
    """
    INTERNAL = "internal"
    MEMORY   = "memory"
    SEARCH   = "search"
    HYBRID   = "hybrid"


@dataclass
class UserContext:
    """Placeholder user context loaded from memory."""
    user_id: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    conversation_summary: Optional[str] = None
    session_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchDecision:
    """Result from the SearchDetector stage."""
    required: bool = False
    reason: str = "no search trigger detected"


@dataclass
class CriticResult:
    """Result from the Critic review stage."""
    passed: bool = True
    issues: List[str] = field(default_factory=list)
    degraded: bool = False


@dataclass
class PipelineContext:
    """
    Immutable-by-convention context object that flows through
    every stage of the pipeline, accumulating results.
    """
    # ── Inputs ──────────────────────────────────────────────────────────────
    request_id: str = ""
    user_id: Optional[str] = None          # stable identifier from frontend / auth
    messages: List[Dict[str, Any]] = field(default_factory=list)
    model: str = ""
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    stream: bool = False
    raw_request: Optional[Any] = None

    # ── Stage Outputs ────────────────────────────────────────────────────────
    intent: str = "general"
    user_context: UserContext = field(default_factory=UserContext)
    search_decision: SearchDecision = field(default_factory=SearchDecision)
    search_response: Optional[Any] = None    # SearchResponse from SearchEngine
    agent_selection: Optional[Any] = None    # AgentSelection (Phase 9)
    agent_system_prompt: Optional[str] = None  # injected by selected agent (Phase 9)
    selected_provider: Optional[str] = None
    selected_provider_instance: Optional[Any] = None
    provider_response: Optional[Any] = None   # ProviderResponse
    critic_result: CriticResult = field(default_factory=CriticResult)
    conversation_context: Optional[Any] = None  # ConversationContext (Phase 7)
    quality_result: Optional[Any] = None         # QualityResult (Phase 7)
    formatted_response: Optional[Any] = None   # ChatCompletionResponse
    memory_facts: List[str] = field(default_factory=list)
    routing_strategy: RoutingStrategy = RoutingStrategy.INTERNAL
    # Citations extracted from search results — appended to the final response
    search_citations: List[Dict[str, str]] = field(default_factory=list)

    # ── Errors ───────────────────────────────────────────────────────────────
    errors: List[str] = field(default_factory=list)
    degraded: bool = False

    # ── Timings (filled by metrics collector) ────────────────────────────────
    timings: Dict[str, float] = field(default_factory=dict)
