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
    circuit_threshold:  int = 3    # failures before circuit opens
    circuit_cooldown:   int = 60   # seconds before retry

    # Default max output tokens (latency cap)
    default_max_tokens: int = 450
