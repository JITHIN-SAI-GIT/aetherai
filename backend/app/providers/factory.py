"""
Provider factory — builds a ProviderManager (circuit-breaker-aware fallback chain).
Priority order: Groq-1 → Groq-2 → Gemini → OpenRouter
"""
from .manager import ProviderManager, ProviderEntry
from .circuit_breaker import CircuitBreaker
from .config import ProviderConfig
from .implementations.groq_provider import GroqProvider
from .implementations.groq2_provider import Groq2Provider
from .implementations.gemini_provider import GeminiProvider
from .implementations.openrouter_provider import OpenRouterProvider


def create_provider_manager(config: ProviderConfig) -> ProviderManager:
    """
    Instantiate all configured providers in priority order.
    Each gets its own CircuitBreaker with settings from config.
    """
    provider_map = {
        "groq":       GroqProvider,
        "groq2":      Groq2Provider,
        "gemini":     GeminiProvider,
        "openrouter": OpenRouterProvider,
    }

    entries = []
    for name in config.provider_priority:
        if name not in config.providers_enabled:
            continue
        cls = provider_map.get(name)
        if cls is None:
            continue
        entries.append(
            ProviderEntry(
                provider=cls(),
                breaker=CircuitBreaker(
                    failure_threshold=config.circuit_threshold,
                    cooldown_seconds=config.circuit_cooldown,
                ),
            )
        )

    return ProviderManager(entries=entries)


# ── Legacy shim — keep create_registry working for tests that import it ────
from .registry import ProviderRegistry
from .implementations.openai_provider import OpenAIProvider
from .implementations.anthropic_provider import AnthropicProvider

def create_registry(config: ProviderConfig) -> ProviderRegistry:
    """Backward-compatible shim used by tests and verify_providers.py."""
    registry = ProviderRegistry(config)
    if "openai" in config.providers_enabled:
        registry.register("openai", OpenAIProvider())
    if "anthropic" in config.providers_enabled:
        registry.register("anthropic", AnthropicProvider())
    if "gemini" in config.providers_enabled:
        registry.register("gemini", GeminiProvider())
    if "groq" in config.providers_enabled:
        registry.register("groq", GroqProvider())
    if "groq2" in config.providers_enabled:
        registry.register("groq2", Groq2Provider())
    if "openrouter" in config.providers_enabled:
        registry.register("openrouter", OpenRouterProvider())
    return registry
