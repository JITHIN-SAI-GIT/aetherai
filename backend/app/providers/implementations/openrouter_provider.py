"""
OpenRouterProvider — uses OPENROUTER_API_KEY via OpenAI-compatible API.
Timeout: 4.5 seconds.
"""
import time
import logging
from typing import List, Dict, Any, AsyncGenerator
import openai
from openai import AsyncOpenAI
from app.providers.models import ProviderResponse
from app.providers.exceptions import ProviderError, ProviderTimeoutError, ProviderRateLimitError, ProviderAuthError
from app.config.settings import get_settings

logger = logging.getLogger("provider.openrouter")

_TIMEOUT = 4.5  # seconds


class OpenRouterProvider:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openrouter_api_key
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            timeout=_TIMEOUT,
            max_retries=0,
            default_headers={
                "HTTP-Referer": "https://aether-ai.app",
                "X-Title": "AETHER AI",
            },
        ) if self.api_key else None
        self.models = [
            "meta-llama/llama-3.3-70b-instruct",
            "meta-llama/llama-3.1-8b-instruct",
            "google/gemini-1.5-flash",
        ]

    def name(self) -> str:
        return "openrouter"

    def _handle_error(self, e: Exception):
        if isinstance(e, openai.RateLimitError):
            raise ProviderRateLimitError(str(e))
        elif isinstance(e, openai.AuthenticationError):
            raise ProviderAuthError(str(e))
        elif isinstance(e, (openai.APITimeoutError, openai.APIConnectionError)):
            raise ProviderTimeoutError(str(e))
        raise ProviderError(str(e))

    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse:
        if not self.client:
            raise ProviderAuthError("OpenRouter API key (OPENROUTER_API_KEY) not configured")
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
            raise ProviderAuthError("OpenRouter API key not configured")
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
        return (input_tokens * 1.0 / 1_000_000) + (output_tokens * 3.0 / 1_000_000)
