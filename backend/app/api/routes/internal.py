from fastapi import APIRouter, Depends
from app.providers.metrics import global_metrics
from app.providers.health import HealthTracker
from app.search.metrics import search_metrics
from app.memory.metrics import memory_metrics
from app.memory.storage import MockStorage
from app.memory.privacy import PrivacyManager
from app.security.metrics import security_metrics
from app.security.audit import audit_logger
from app.security.policies import POLICIES
from app.core.dependencies import get_performance_metrics, get_connection_pool
from app.performance.latency import LatencyTracker

router = APIRouter(tags=["internal"])
global_health = HealthTracker()
_mock_storage = MockStorage()
_privacy_mgr = PrivacyManager(_mock_storage)

@router.get("/internal/providers")
async def get_providers():
    return {"status": "ok", "providers": ["openai", "anthropic", "gemini", "groq", "openrouter"]}

@router.get("/internal/providers/health")
async def get_providers_health():
    return {"openai": global_health.get_status()}

@router.get("/internal/providers/metrics")
async def get_providers_metrics():
    return global_metrics.get_snapshot()

@router.get("/internal/search/cache")
async def get_search_cache():
    return search_metrics.snapshot()

@router.get("/internal/search/metrics")
async def get_search_metrics():
    return search_metrics.snapshot()

@router.get("/internal/search/providers")
async def get_search_providers():
    return {"providers": ["duckduckgo", "brave", "tavily", "serpapi"]}

@router.get("/internal/memory/metrics")
async def get_memory_metrics():
    return memory_metrics.snapshot()

@router.get("/internal/memory/profile")
async def get_memory_profile(user_id: str = "default"):
    return await _mock_storage.export(user_id)

@router.get("/internal/memory/preferences")
async def get_memory_preferences(user_id: str = "default"):
    raw = await _mock_storage.get(user_id, "__preferences__")
    return raw or {}

@router.get("/internal/memory/session")
async def get_memory_session():
    return {"session_count": 0}

@router.get("/internal/memory/export")
async def export_memory(user_id: str = "default"):
    return await _privacy_mgr.export_all(user_id)

@router.delete("/internal/memory/delete")
async def delete_memory(user_id: str, confirmed: bool = False):
    await _privacy_mgr.delete_all(user_id, confirmed=confirmed)
    return {"deleted": True, "user_id": user_id}

@router.get("/internal/security/metrics")
async def get_security_metrics():
    return security_metrics.snapshot()

@router.get("/internal/security/events")
async def get_security_events(n: int = 50):
    return {"events": audit_logger.recent(n)}

@router.get("/internal/security/policies")
async def get_security_policies():
    return {
        "max_message_length": POLICIES.max_message_length,
        "max_messages_per_request": POLICIES.max_messages_per_request,
        "rate_limit_ip_per_minute": POLICIES.rate_limit_ip_per_minute,
        "rate_limit_user_per_minute": POLICIES.rate_limit_user_per_minute,
        "block_violence": POLICIES.block_violence,
        "block_self_harm": POLICIES.block_self_harm,
        "block_illegal": POLICIES.block_illegal,
        "block_sexual": POLICIES.block_sexual,
        "block_hate": POLICIES.block_hate,
        "api_keys_enabled": POLICIES.api_keys_enabled,
    }

@router.get("/internal/performance")
async def get_performance_overview():
    """Full performance metrics snapshot."""
    metrics = get_performance_metrics()
    return metrics.snapshot()

@router.get("/internal/performance/latency")
async def get_performance_latency():
    """Per-stage latency percentiles and bottleneck report."""
    metrics = get_performance_metrics()
    tracker = LatencyTracker(metrics)
    return tracker.bottleneck_report()

@router.get("/internal/performance/cache")
async def get_performance_cache():
    """Cache efficiency metrics."""
    metrics = get_performance_metrics()
    snap = metrics.snapshot()
    return {
        "cache_hit_rate": snap["cache_hit_rate"],
        "cache_hits": snap["cache_hits"],
        "cache_misses": snap["cache_misses"],
    }

@router.get("/internal/performance/pool")
async def get_connection_pool_status():
    """Connection pool readiness status."""
    pool = get_connection_pool()
    return {"pool_ready": pool.is_ready}
