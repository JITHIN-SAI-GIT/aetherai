"""
Groq2Provider — second Groq key (GROQ_API_KEY_2).
Identical to GroqProvider but reads GROQ_API_KEY_2 so the two slots
can use different keys and hit different rate limits independently.
Timeout: 2.5 seconds.
"""
import time
import logging
from typing import List, Dict, Any, AsyncGenerator
import groq
from groq import AsyncGroq
from app.providers.models import ProviderResponse
from app.providers.exceptions import ProviderError, ProviderTimeoutError, ProviderRateLimitError, ProviderAuthError
from app.config.settings import get_settings

logger = logging.getLogger("provider.groq2")

_TIMEOUT = 5.0  # raised from 2.5s — see groq_provider.py for rationale


class Groq2Provider:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.groq_api_key_2
        # Fall back to primary key if secondary is not set — still a valid
        # fallback provider (different circuit breaker = independent health)
        if not self.api_key:
            self.api_key = settings.groq_api_key
        self.client = AsyncGroq(api_key=self.api_key, timeout=_TIMEOUT, max_retries=0) if self.api_key else None
        self.models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]

    def name(self) -> str:
        return "groq2"

    def _handle_error(self, e: Exception):
        if isinstance(e, groq.RateLimitError):
            raise ProviderRateLimitError(str(e))
        elif isinstance(e, groq.AuthenticationError):
            raise ProviderAuthError(str(e))
        elif isinstance(e, (groq.APITimeoutError, groq.APIConnectionError)):
            raise ProviderTimeoutError(str(e))
        raise ProviderError(str(e))

    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse:
        if not self.client:
            raise ProviderAuthError("Groq secondary API key (GROQ_API_KEY_2) not configured")
        start = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=model, messages=messages, stream=False, **kwargs,
            )
            latency = int((time.time() - start) * 1000)
            return ProviderResponse(
                provider=self.name(),
                model=model,
                content=response.choices[0].message.content or "",
                finish_reason=response.choices[0].finish_reason or "stop",
                usage={
                    "prompt_tokens":     response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens":      response.usage.total_tokens if response.usage else 0,
                },
                latency_ms=latency,
                status=200,
            )
        except Exception as e:
            self._handle_error(e)

    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        if not self.client:
            raise ProviderAuthError("Groq secondary API key not configured")
        try:
            stream = await self.client.chat.completions.create(
                model=model, messages=messages, stream=True, **kwargs,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            self._handle_error(e)

    async def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False

    def supports_streaming(self) -> bool:
        return True

    def model_list(self) -> List[str]:
        return self.models

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        rates = {
            "llama-3.3-70b-versatile": (0.59, 0.79),
            "llama-3.1-8b-instant":    (0.05, 0.08),
            "mixtral-8x7b-32768":      (0.24, 0.24),
        }
        rate = rates.get(model, (0.0, 0.0))
        return (input_tokens * rate[0] / 1_000_000) + (output_tokens * rate[1] / 1_000_000)
