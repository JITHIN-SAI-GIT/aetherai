import os

base_path = r"c:\Users\jithin sai\OneDrive\Desktop\finalbot\backend"

directories = [
    "app/pipeline",
    "tests/pipeline",
]

files = {
    # ─────────────────────────────────────────────────────────────────────────────
    # INTERFACES
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/interfaces.py": '''from typing import Protocol, runtime_checkable
from .context import PipelineContext


@runtime_checkable
class IntentDetectorProtocol(Protocol):
    def detect(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class ContextLoaderProtocol(Protocol):
    async def load(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class SearchDetectorProtocol(Protocol):
    def detect(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class ProviderRouterProtocol(Protocol):
    def route(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class CriticProtocol(Protocol):
    def review(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class FormatterProtocol(Protocol):
    def format(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class MemoryUpdaterProtocol(Protocol):
    async def update(self, context: PipelineContext) -> PipelineContext:
        ...
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # EXCEPTIONS
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/exceptions.py": '''class PipelineError(Exception):
    """Base class for all pipeline errors."""
    def __init__(self, stage: str, message: str):
        self.stage = stage
        self.message = message
        super().__init__(f"[{stage}] {message}")


class PipelineValidationError(PipelineError):
    """Raised when request validation fails inside the pipeline."""
    pass


class PipelineRoutingError(PipelineError):
    """Raised when no provider is available to handle the request."""
    pass


class PipelineStageError(PipelineError):
    """Raised when a generic pipeline stage encounters an unrecoverable error."""
    pass
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # CONTEXT
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/context.py": '''from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


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
    selected_provider: Optional[str] = None
    provider_response: Optional[Any] = None   # ProviderResponse
    critic_result: CriticResult = field(default_factory=CriticResult)
    formatted_response: Optional[Any] = None   # ChatCompletionResponse
    memory_facts: List[str] = field(default_factory=list)

    # ── Errors ───────────────────────────────────────────────────────────────
    errors: List[str] = field(default_factory=list)
    degraded: bool = False

    # ── Timings (filled by metrics collector) ────────────────────────────────
    timings: Dict[str, float] = field(default_factory=dict)
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # METRICS
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/metrics.py": '''import time
import logging
from contextlib import contextmanager
from .context import PipelineContext

logger = logging.getLogger("pipeline.metrics")


@contextmanager
def track_stage(context: PipelineContext, stage_name: str):
    """
    Context manager that measures execution time of a named pipeline stage
    and writes the result (ms) into PipelineContext.timings.
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        context.timings[stage_name] = round(elapsed_ms, 3)
        logger.info(
            "Stage complete",
            extra={
                "request_id": context.request_id,
                "stage": stage_name,
                "duration_ms": elapsed_ms,
            }
        )
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # INTENT DETECTOR
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/intent.py": '''import logging
from typing import Dict, List
from .context import PipelineContext

logger = logging.getLogger("pipeline.intent")

# Intent keyword registry – easy to extend by adding new entries
INTENT_RULES: Dict[str, List[str]] = {
    "coding":               ["code", "function", "class", "bug", "debug", "python", "javascript",
                             "implement", "algorithm", "script", "syntax", "compiler"],
    "reasoning":            ["why", "explain", "reason", "because", "cause", "logic", "analyze",
                             "argument", "inference", "deduce"],
    "math":                 ["calculate", "solve", "equation", "integral", "derivative", "proof",
                             "formula", "algebra", "geometry", "matrix", "sum"],
    "creative":             ["write", "story", "poem", "imagine", "creative", "fiction", "rhyme",
                             "narrative", "compose"],
    "translation":          ["translate", "in french", "in spanish", "in german", "language",
                             "convert to", "in japanese"],
    "search_required":      ["latest", "current", "today", "news", "2024", "2025", "recent",
                             "now", "live", "real-time"],
    "clarification_required": ["what do you mean", "clarify", "not clear", "elaborate", "rephrase"],
    "tool_request":         ["call", "use tool", "function call", "execute", "run", "invoke"],
}


class IntentDetector:
    """
    Rule-based intent classification strategy.
    Scans the last user message for keyword patterns.
    Defaults to 'chat'. Easy to replace with an ML strategy later.
    """

    def detect(self, context: PipelineContext) -> PipelineContext:
        last_user_message = self._get_last_user_message(context.messages)
        intent = self._classify(last_user_message)
        context.intent = intent

        logger.info(
            "Intent detected",
            extra={
                "request_id": context.request_id,
                "intent": intent,
            }
        )
        return context

    # ── Private helpers ──────────────────────────────────────────────────────

    def _get_last_user_message(self, messages: List[Dict]) -> str:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                return content if isinstance(content, str) else ""
        return ""

    def _classify(self, text: str) -> str:
        lowered = text.lower()
        for intent, keywords in INTENT_RULES.items():
            if any(kw in lowered for kw in keywords):
                return intent
        return "chat"
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # SEARCH DETECTOR
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/search_detector.py": '''import logging
from .context import PipelineContext, SearchDecision

logger = logging.getLogger("pipeline.search_detector")


class SearchDetector:
    """
    Placeholder search detector.
    Returns a decision object without performing any real search.
    Future: integrate web search APIs based on intent and user preferences.
    """

    def detect(self, context: PipelineContext) -> PipelineContext:
        required = context.intent == "search_required"
        reason = "intent classified as search_required" if required else "no search trigger detected"
        context.search_decision = SearchDecision(required=required, reason=reason)

        logger.info(
            "Search decision",
            extra={
                "request_id": context.request_id,
                "search_required": required,
                "reason": reason,
            }
        )
        return context
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # CONTEXT / MEMORY LOADER
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/memory_loader.py": '''import logging
from .context import PipelineContext, UserContext

logger = logging.getLogger("pipeline.memory_loader")


class ContextLoader:
    """
    Placeholder context loader.
    Returns a mock UserContext without touching any database.
    Future: fetch from PostgreSQL / Redis based on session_id / user_id.
    """

    async def load(self, context: PipelineContext) -> PipelineContext:
        # Placeholder: return empty context; real loader will query DB
        context.user_context = UserContext(
            user_id=context.request_id,
            preferences={"theme": "dark", "language": "en"},
            conversation_summary=None,
            session_metadata={},
        )

        logger.info(
            "Context loaded",
            extra={
                "request_id": context.request_id,
                "user_id": context.user_context.user_id,
            }
        )
        return context
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # PROVIDER ROUTER
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/router.py": '''import logging
from .context import PipelineContext
from .exceptions import PipelineRoutingError
from app.providers.registry import ProviderRegistry

logger = logging.getLogger("pipeline.router")


class ProviderRouter:
    """
    Consumes the Phase 2 ProviderRegistry to select the best available provider.
    Respects priority order, health state, and circuit breaker state.
    """

    def __init__(self, registry: ProviderRegistry):
        self._registry = registry

    def route(self, context: PipelineContext) -> PipelineContext:
        providers = self._registry.get_priority_list()

        if not providers:
            raise PipelineRoutingError(
                stage="ProviderRouter",
                message="No providers registered in the registry."
            )

        # Select first provider in priority list (circuit breaker will gate in manager)
        selected = providers[0]
        context.selected_provider = selected.name()

        logger.info(
            "Provider selected",
            extra={
                "request_id": context.request_id,
                "provider": context.selected_provider,
            }
        )
        return context
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # DECISION
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/decision.py": '''from dataclasses import dataclass


@dataclass
class IntentDecision:
    """Carries the result of intent detection for logging purposes."""
    intent: str
    confidence: float = 1.0
    source: str = "rule_based"
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # CRITIC
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/critic.py": '''import logging
from typing import List
from .context import PipelineContext, CriticResult

logger = logging.getLogger("pipeline.critic")

VALID_FINISH_REASONS = {"stop", "length", "tool_calls", "content_filter"}


class Critic:
    """
    Reviews the ProviderResponse for quality and correctness.
    Substitutes a graceful degraded placeholder if the response is invalid.
    """

    def review(self, context: PipelineContext) -> PipelineContext:
        issues: List[str] = []
        resp = context.provider_response

        if resp is None:
            issues.append("ProviderResponse is None")
        else:
            if not resp.content or not resp.content.strip():
                issues.append("Response content is empty")
            if resp.finish_reason not in VALID_FINISH_REASONS:
                issues.append(f"Invalid finish_reason: {resp.finish_reason!r}")
            if resp.status >= 400:
                issues.append(f"Provider returned error status: {resp.status}")

        passed = len(issues) == 0
        degraded = not passed

        if degraded:
            # Substitute a graceful degraded response rather than crashing
            from app.providers.models import ProviderResponse
            context.provider_response = ProviderResponse(
                provider=context.selected_provider or "unknown",
                model=context.model,
                content="I'm sorry, I was unable to generate a response at this time. Please try again.",
                finish_reason="stop",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency_ms=0,
                status=200,
            )
            context.degraded = True

        context.critic_result = CriticResult(passed=passed, issues=issues, degraded=degraded)

        logger.info(
            "Critic review complete",
            extra={
                "request_id": context.request_id,
                "passed": passed,
                "issues": issues,
                "degraded": degraded,
            }
        )
        return context
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # FORMATTER
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/formatter.py": '''import logging
from .context import PipelineContext
from app.api.v1.serializers import serialize_provider_response

logger = logging.getLogger("pipeline.formatter")


class Formatter:
    """
    Converts ProviderResponse → ChatCompletionResponse.
    Reuses Phase 3 serializers to guarantee schema conformity.
    """

    def format(self, context: PipelineContext) -> PipelineContext:
        context.formatted_response = serialize_provider_response(context.provider_response)
        logger.info(
            "Response formatted",
            extra={
                "request_id": context.request_id,
                "response_id": context.formatted_response.id,
            }
        )
        return context
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # MEMORY UPDATER
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/memory_updater.py": '''import logging
from typing import List
from .context import PipelineContext

logger = logging.getLogger("pipeline.memory_updater")


class MemoryUpdater:
    """
    Placeholder memory updater.
    Extracts mock facts/preferences from the context but does NOT persist them.
    Future: write to pgvector memory table via background task.
    """

    async def update(self, context: PipelineContext) -> PipelineContext:
        # Placeholder: produce mock extracted facts
        facts: List[str] = []
        if context.intent == "coding":
            facts.append("User is interested in coding topics.")
        if context.intent == "math":
            facts.append("User asked about a math problem.")

        context.memory_facts = facts

        logger.info(
            "Memory update triggered",
            extra={
                "request_id": context.request_id,
                "facts_extracted": len(facts),
            }
        )
        return context
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # PIPELINE EXECUTOR
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/pipeline.py": '''import logging
import time
from .context import PipelineContext
from .metrics import track_stage
from .exceptions import PipelineError

logger = logging.getLogger("pipeline")


class Pipeline:
    """
    Assembles and executes the ordered chain of pipeline stages.
    Each stage receives the context and returns the mutated context.
    Stage failures are caught and recorded without crashing the pipeline.
    """

    def __init__(
        self,
        intent_detector,
        context_loader,
        search_detector,
        provider_router,
        provider_manager,
        critic,
        formatter,
        memory_updater,
    ):
        self.intent_detector = intent_detector
        self.context_loader = context_loader
        self.search_detector = search_detector
        self.provider_router = provider_router
        self.provider_manager = provider_manager
        self.critic = critic
        self.formatter = formatter
        self.memory_updater = memory_updater

    async def run(self, context: PipelineContext) -> PipelineContext:
        pipeline_start = time.perf_counter()

        # ── Stage 1: Intent Detection ─────────────────────────────────────────
        with track_stage(context, "intent_detection"):
            context = self.intent_detector.detect(context)

        # ── Stage 2: Load Session Context ─────────────────────────────────────
        with track_stage(context, "context_loading"):
            context = await self.context_loader.load(context)

        # ── Stage 3: Search Decision ──────────────────────────────────────────
        with track_stage(context, "search_detection"):
            context = self.search_detector.detect(context)

        # ── Stage 4: Provider Routing ─────────────────────────────────────────
        with track_stage(context, "provider_routing"):
            try:
                context = self.provider_router.route(context)
            except PipelineError as e:
                context.errors.append(str(e))
                context.degraded = True
                context.selected_provider = "none"

        # ── Stage 5: Call Provider Manager ────────────────────────────────────
        with track_stage(context, "provider_call"):
            try:
                context.provider_response = await self.provider_manager.generate(
                    context.messages, model=context.model
                )
            except Exception as e:
                context.errors.append(f"ProviderManager error: {e}")
                # Inject a null response; critic will handle degradation
                context.provider_response = None

        # ── Stage 6: Critic Review ─────────────────────────────────────────────
        with track_stage(context, "critic_review"):
            context = self.critic.review(context)

        # ── Stage 7: Format Response ───────────────────────────────────────────
        with track_stage(context, "formatting"):
            context = self.formatter.format(context)

        # ── Stage 8: Memory Update (async fire-and-forget placeholder) ─────────
        with track_stage(context, "memory_update"):
            context = await self.memory_updater.update(context)

        # ── Record total pipeline duration ────────────────────────────────────
        context.timings["total_pipeline"] = round(
            (time.perf_counter() - pipeline_start) * 1000, 3
        )

        logger.info(
            "Pipeline complete",
            extra={
                "request_id": context.request_id,
                "intent": context.intent,
                "provider": context.selected_provider,
                "degraded": context.degraded,
                "timings_ms": context.timings,
            }
        )
        return context
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # ORCHESTRATOR
    # ─────────────────────────────────────────────────────────────────────────────
    "app/pipeline/orchestrator.py": '''import uuid
import logging
from app.api.v1.schemas.chat_completion import ChatCompletionRequest, ChatCompletionResponse
from app.providers.models import ProviderResponse
from .context import PipelineContext
from .pipeline import Pipeline

logger = logging.getLogger("pipeline.orchestrator")


class Orchestrator:
    """
    Single top-level entry point for all chat requests.
    API routes call ONLY orchestrator.run() — no business logic lives in routes.
    """

    def __init__(self, pipeline: Pipeline):
        self._pipeline = pipeline

    async def run(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        request_id = str(uuid.uuid4())

        logger.info(
            "Pipeline invoked",
            extra={
                "request_id": request_id,
                "model": request.model,
                "stream": request.stream,
            }
        )

        context = PipelineContext(
            request_id=request_id,
            messages=[m.model_dump() for m in request.messages],
            model=request.model,
            temperature=request.temperature or 1.0,
            max_tokens=request.max_tokens,
            stream=request.stream or False,
            raw_request=request,
        )

        context = await self._pipeline.run(context)
        return context.formatted_response
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # DEPENDENCY WIRING – updated dependencies.py
    # ─────────────────────────────────────────────────────────────────────────────
    "app/core/dependencies.py": '''"""
Dependency Injection Container.
Wire all pipeline stages here; FastAPI injects the Orchestrator into routes.
"""
from functools import lru_cache
from app.providers.config import ProviderConfig
from app.providers.factory import create_registry
from app.providers.manager import ProviderManager
from app.pipeline.intent import IntentDetector
from app.pipeline.memory_loader import ContextLoader
from app.pipeline.search_detector import SearchDetector
from app.pipeline.router import ProviderRouter
from app.pipeline.critic import Critic
from app.pipeline.formatter import Formatter
from app.pipeline.memory_updater import MemoryUpdater
from app.pipeline.pipeline import Pipeline
from app.pipeline.orchestrator import Orchestrator


@lru_cache()
def get_provider_config() -> ProviderConfig:
    return ProviderConfig()


@lru_cache()
def get_orchestrator() -> Orchestrator:
    config = get_provider_config()
    registry = create_registry(config)
    manager = ProviderManager(registry)

    pipeline = Pipeline(
        intent_detector=IntentDetector(),
        context_loader=ContextLoader(),
        search_detector=SearchDetector(),
        provider_router=ProviderRouter(registry),
        provider_manager=manager,
        critic=Critic(),
        formatter=Formatter(),
        memory_updater=MemoryUpdater(),
    )
    return Orchestrator(pipeline)
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # UPDATED CHAT ROUTE – routes call orchestrator only
    # ─────────────────────────────────────────────────────────────────────────────
    "app/api/v1/chat.py": '''from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from .schemas.chat_completion import ChatCompletionRequest, ChatCompletionResponse
from .validators import validate_chat_request
from .stream import sse_stream_generator
from app.core.dependencies import get_orchestrator
from app.pipeline.orchestrator import Orchestrator

router = APIRouter(tags=["Chat Completions"])


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    req: ChatCompletionRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    validate_chat_request(req)

    if req.stream:
        return StreamingResponse(sse_stream_generator(req.model), media_type="text/event-stream")

    return await orchestrator.run(req)
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # UPDATED PROVIDER MANAGER – generate now returns a mock ProviderResponse
    # (no real API call; just a placeholder so the pipeline doesn't fail)
    # ─────────────────────────────────────────────────────────────────────────────
    "app/providers/manager.py": '''import logging
from typing import List, Dict, Any
from .registry import ProviderRegistry
from .models import ProviderResponse
from .exceptions import NoAvailableProviderError

logger = logging.getLogger("providers.manager")


class ProviderManager:
    """
    Orchestrates calls to the provider registry.
    Returns a mock ProviderResponse (Phase 4 placeholder — real calls in Phase 5).
    """

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    async def generate(self, messages: List[Dict[str, Any]], model: str = None) -> ProviderResponse:
        providers = self.registry.get_priority_list()

        if not providers:
            raise NoAvailableProviderError("No providers configured.")

        selected = providers[0]
        provider_name = selected.name()

        logger.info("Provider selected", extra={"provider": provider_name, "model": model})

        # ── Phase 4 placeholder ─────────────────────────────────────────────
        return ProviderResponse(
            provider=provider_name,
            model=model or "unknown",
            content="This is a Phase 4 pipeline placeholder response.",
            finish_reason="stop",
            usage={"prompt_tokens": 12, "completion_tokens": 12, "total_tokens": 24},
            latency_ms=5,
            status=200,
        )
''',

    # ─────────────────────────────────────────────────────────────────────────────
    # TESTS
    # ─────────────────────────────────────────────────────────────────────────────
    "tests/pipeline/__init__.py": "",

    "tests/pipeline/test_intent.py": '''from app.pipeline.intent import IntentDetector
from app.pipeline.context import PipelineContext


def _make_context(content: str) -> PipelineContext:
    return PipelineContext(
        request_id="test",
        messages=[{"role": "user", "content": content}],
        model="gpt-4-turbo",
    )


def test_coding_intent():
    ctx = _make_context("Can you write a Python function to reverse a string?")
    result = IntentDetector().detect(ctx)
    assert result.intent == "coding"


def test_math_intent():
    ctx = _make_context("Can you solve this equation for me?")
    result = IntentDetector().detect(ctx)
    assert result.intent == "math"


def test_search_intent():
    ctx = _make_context("What is the latest news today?")
    result = IntentDetector().detect(ctx)
    assert result.intent == "search_required"


def test_translation_intent():
    ctx = _make_context("Translate this sentence in French please.")
    result = IntentDetector().detect(ctx)
    assert result.intent == "translation"


def test_default_chat_intent():
    ctx = _make_context("Hey, how are you doing today?")
    result = IntentDetector().detect(ctx)
    assert result.intent == "chat"
''',

    "tests/pipeline/test_critic.py": '''import pytest
from app.pipeline.critic import Critic
from app.pipeline.context import PipelineContext
from app.providers.models import ProviderResponse


def _response(**kwargs) -> ProviderResponse:
    defaults = dict(
        provider="openai", model="gpt-4", content="Hello!",
        finish_reason="stop", usage={}, latency_ms=10, status=200
    )
    defaults.update(kwargs)
    return ProviderResponse(**defaults)


def test_critic_passes_valid_response():
    ctx = PipelineContext(request_id="test", model="gpt-4",
                          provider_response=_response())
    result = Critic().review(ctx)
    assert result.critic_result.passed is True
    assert result.degraded is False


def test_critic_fails_empty_content():
    ctx = PipelineContext(request_id="test", model="gpt-4",
                          provider_response=_response(content=""))
    result = Critic().review(ctx)
    assert result.critic_result.passed is False
    assert result.degraded is True
    assert result.provider_response.content  # degraded placeholder injected


def test_critic_fails_none_response():
    ctx = PipelineContext(request_id="test", model="gpt-4", provider_response=None)
    result = Critic().review(ctx)
    assert result.critic_result.passed is False
    assert result.degraded is True


def test_critic_fails_invalid_finish_reason():
    ctx = PipelineContext(request_id="test", model="gpt-4",
                          provider_response=_response(finish_reason="ERROR"))
    result = Critic().review(ctx)
    assert result.critic_result.passed is False
''',

    "tests/pipeline/test_formatter.py": '''from app.pipeline.formatter import Formatter
from app.pipeline.context import PipelineContext
from app.providers.models import ProviderResponse


def test_formatter_produces_openai_schema():
    resp = ProviderResponse(
        provider="openai", model="gpt-4", content="Test content",
        finish_reason="stop", usage={"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
        latency_ms=10, status=200
    )
    ctx = PipelineContext(request_id="test", model="gpt-4", provider_response=resp)
    result = Formatter().format(ctx)

    cr = result.formatted_response
    assert cr.object == "chat.completion"
    assert cr.choices[0].message.content == "Test content"
    assert cr.usage.total_tokens == 10
    assert cr.id.startswith("chatcmpl-")
''',

    "tests/pipeline/test_routing.py": '''from app.pipeline.router import ProviderRouter
from app.pipeline.context import PipelineContext
from app.providers.registry import ProviderRegistry
from app.providers.config import ProviderConfig
from app.providers.implementations.openai_provider import OpenAIProvider


def test_provider_router_selects_first_priority():
    config = ProviderConfig(provider_priority=["openai"])
    registry = ProviderRegistry(config)
    registry.register("openai", OpenAIProvider())

    ctx = PipelineContext(request_id="test", model="gpt-4")
    result = ProviderRouter(registry).route(ctx)
    assert result.selected_provider == "openai"


def test_provider_router_raises_on_empty_registry():
    import pytest
    from app.pipeline.exceptions import PipelineRoutingError
    config = ProviderConfig(provider_priority=[])
    registry = ProviderRegistry(config)

    ctx = PipelineContext(request_id="test", model="gpt-4")
    with pytest.raises(PipelineRoutingError):
        ProviderRouter(registry).route(ctx)
''',

    "tests/pipeline/test_pipeline.py": '''import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_pipeline_non_stream_e2e():
    """End-to-end: POST /v1/chat/completions flows through the full pipeline."""
    payload = {
        "model": "gpt-4-turbo",
        "messages": [{"role": "user", "content": "Hello pipeline!"}],
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert data["choices"][0]["message"]["content"]


def test_pipeline_invalid_role_returns_400():
    payload = {
        "model": "gpt-4-turbo",
        "messages": [{"role": "bot", "content": "Hi"}],
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 400
    assert resp.json()["error"]["type"] == "invalid_request_error"
''',
}

# ── Create directories ──────────────────────────────────────────────────────────
for d in directories:
    dir_path = os.path.join(base_path, d)
    os.makedirs(dir_path, exist_ok=True)

# ── Ensure __init__.py exists in every new directory ───────────────────────────
for d in directories:
    parts = d.split("/")
    for i in range(1, len(parts) + 1):
        init_dir = os.path.join(base_path, *parts[:i])
        init_file = os.path.join(init_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "a").close()

# ── Write all files ─────────────────────────────────────────────────────────────
for file_path, content in files.items():
    full_path = os.path.join(base_path, file_path)
    os.makedirs(os.path.dirname(full_path) or base_path, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Phase 4 skeleton generated successfully.")
