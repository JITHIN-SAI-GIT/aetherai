"""
Dependency Injection Container.
All pipeline stages are wired here; FastAPI injects the Orchestrator into routes.

Changes vs. original:
- Uses ProviderManager (circuit-breaker fallback chain) instead of ProviderRouter
- MemoryManager is now passed into ContextLoader and MemoryUpdater (Fix 7)
- ProviderConfig now sets priority: groq → groq2 → gemini → openrouter
"""
from functools import lru_cache

from app.providers.config import ProviderConfig
from app.providers.factory import create_provider_manager

from app.pipeline.intent import IntentDetector
from app.pipeline.memory_loader import ContextLoader
from app.pipeline.search_detector import SearchDetector
from app.pipeline.search_executor import SearchExecutor
from app.pipeline.search_injector import SearchInjector
from app.pipeline.citation_appender import CitationAppender
from app.pipeline.critic import Critic
from app.pipeline.formatter import Formatter
from app.pipeline.memory_updater import MemoryUpdater
from app.pipeline.pipeline import Pipeline
from app.pipeline.orchestrator import Orchestrator

from app.conversation.conversation_manager import ConversationManager
from app.agents.factory import AgentFactory
from app.agents.manager import AgentManager

from app.performance.connection_pool import ConnectionPool
from app.performance.metrics import PerformanceMetrics
from app.performance.config import PerformanceConfig
from app.pipeline import metrics as pipeline_metrics_module

# ── Search engine ──────────────────────────────────────────────────────────
from app.search.config import SearchSettings
from app.search.registry import SearchProviderRegistry
from app.search.cache import SearchCache
from app.search.normalizer import QueryNormalizer
from app.search.summarizer import Summarizer
from app.search.metrics import SearchMetrics
from app.search.engine import SearchEngine
from app.search.providers.duckduckgo import DuckDuckGoSearchProvider
from app.search.providers.brave import BraveSearchProvider
from app.search.providers.tavily import TavilySearchProvider
from app.search.providers.serpapi import SerpAPISearchProvider

# ── Memory subsystem ───────────────────────────────────────────────────────
from app.memory.manager import MemoryManager
from app.memory.storage import MongoStorage
from app.memory.extractor import FactExtractor
from app.memory.summarizer import ConversationSummarizer
from app.memory.session import SessionMemory
from app.memory.profile import ProfileManager
from app.memory.preferences import PreferencesManager
from app.memory.cleanup import MemoryCleanup
from app.memory.privacy import PrivacyManager
from app.memory.metrics import MemoryMetrics


# ── Infrastructure ─────────────────────────────────────────────────────────

@lru_cache()
def get_provider_config() -> ProviderConfig:
    return ProviderConfig()


@lru_cache()
def get_performance_config() -> PerformanceConfig:
    return PerformanceConfig()


@lru_cache()
def get_connection_pool() -> ConnectionPool:
    return ConnectionPool(config=get_performance_config())


@lru_cache()
def get_performance_metrics() -> PerformanceMetrics:
    config  = get_performance_config()
    metrics = PerformanceMetrics(window_size=config.latency_window_size)
    pipeline_metrics_module.configure_metrics(metrics)
    return metrics


# ── Search engine ──────────────────────────────────────────────────────────

@lru_cache()
def get_search_settings() -> SearchSettings:
    return SearchSettings()


@lru_cache()
def get_search_engine() -> SearchEngine:
    settings = get_search_settings()
    registry = SearchProviderRegistry(priority=settings.search_provider_priority)
    registry.register(DuckDuckGoSearchProvider())
    registry.register(BraveSearchProvider())
    registry.register(TavilySearchProvider())
    registry.register(SerpAPISearchProvider())
    return SearchEngine(
        registry=registry,
        cache=SearchCache(redis_url=settings.redis_url),
        normalizer=QueryNormalizer(),
        summarizer=Summarizer(),
        metrics=SearchMetrics(),
        max_results=settings.max_results,
    )


# ── Memory subsystem ───────────────────────────────────────────────────────

@lru_cache()
def get_memory_manager() -> MemoryManager:
    """
    Build and return the singleton MemoryManager.
    All sub-components use MongoDB via MongoStorage.
    """
    storage  = MongoStorage()
    session  = SessionMemory(max_turns=20, ttl_seconds=3600)
    cleanup  = MemoryCleanup(storage=storage)
    return MemoryManager(
        storage=storage,
        extractor=FactExtractor(),
        summarizer=ConversationSummarizer(),
        session=session,
        profile_mgr=ProfileManager(storage=storage),
        prefs_mgr=PreferencesManager(storage=storage),
        cleanup=cleanup,
        privacy=PrivacyManager(storage=storage),
        metrics=MemoryMetrics(),
    )


# ── Main orchestrator ───────────────────────────────────────────────────────

@lru_cache()
def get_orchestrator() -> Orchestrator:
    config           = get_provider_config()
    provider_manager = create_provider_manager(config)   # circuit-breaker chain
    agent_registry   = AgentFactory.build_default_registry()
    search_engine    = get_search_engine()
    memory_manager   = get_memory_manager()              # Fix 7: wired into loaders

    pipeline = Pipeline(
        intent_detector=IntentDetector(),
        context_loader=ContextLoader(memory_manager=memory_manager),     # Fix 7
        search_detector=SearchDetector(),
        search_executor=SearchExecutor(engine=search_engine),
        agent_manager=AgentManager(agent_registry),
        provider_manager=provider_manager,                                # Fix 1
        critic=Critic(),
        conversation_manager=ConversationManager(),
        search_injector=SearchInjector(),
        formatter=Formatter(),
        citation_appender=CitationAppender(),
        memory_updater=MemoryUpdater(memory_manager=memory_manager),      # Fix 7
    )
    return Orchestrator(pipeline)
