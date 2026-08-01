from pydantic_settings import BaseSettings
from typing import List, Dict

class ProviderConfig(BaseSettings):
    # Priority: Groq-1 → Groq-2 → Gemini → OpenRouter (exactly as spec)
    providers_enabled: List[str]  = ["groq", "groq2", "gemini", "openrouter"]
    provider_priority: List[str]  = ["groq", "groq2", "gemini", "openrouter"]

    # Per-provider timeouts in seconds
    provider_timeouts: Dict[str, float] = {
        "groq":       2.5,
        "groq2":      2.5,
        "gemini":     4.5,
        "openrouter": 4.5,
    }

    # Circuit breaker
    retry_count:        int = 3
    circuit_threshold:  int = 5    # failures before circuit opens (raised from 3 — brief 429 bursts shouldn't lock a provider)
    circuit_cooldown:   int = 15   # seconds before retry (reduced from 60 — recover fast after rate-limit spikes)

    # Default max output tokens (latency cap)
    default_max_tokens: int = 450
