"""
GeminiProvider — uses GEMINI_API_KEY.
Timeout: 4.5 seconds.
"""
import time
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError
from app.providers.models import ProviderResponse
from app.providers.exceptions import ProviderError, ProviderTimeoutError, ProviderRateLimitError, ProviderAuthError
from app.config.settings import get_settings

logger = logging.getLogger("provider.gemini")

_TIMEOUT = 4.5  # seconds


class GeminiProvider:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.models = ["gemini-1.5-flash", "gemini-1.5-pro"]

    def name(self) -> str:
        return "gemini"

    def _handle_error(self, e: Exception):
        if isinstance(e, APIError):
            if e.code == 429:
                raise ProviderRateLimitError(str(e))
            elif e.code in (401, 403):
                raise ProviderAuthError(str(e))
            elif e.code in (503, 504):
                raise ProviderTimeoutError(str(e))
        raise ProviderError(str(e))

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> tuple[Optional[str], List[types.Content]]:
        """Convert OpenAI-style messages to Gemini Content types."""
        system_instruction = None
        contents = []
        for msg in messages:
            role    = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = (system_instruction + "\n" + content) if system_instruction else content
            else:
                gemini_role = "user" if role == "user" else "model"
                contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=content)],
                    )
                )
        return system_instruction, contents

    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse:
        if not self.client:
            raise ProviderAuthError("Gemini API key (GEMINI_API_KEY) not configured")

        system_instruction, contents = self._convert_messages(messages)
        start = time.time()

        config_kwargs: Dict[str, Any] = {"request_options": types.RequestOptions(timeout=_TIMEOUT)}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if "temperature" in kwargs:
            config_kwargs["temperature"] = kwargs.pop("temperature")
        if "max_tokens" in kwargs:
            config_kwargs["max_output_tokens"] = kwargs.pop("max_tokens")

        config = types.GenerateContentConfig(**config_kwargs)

        try:
            response = await self.client.aio.models.generate_content(
                model=model, contents=contents, config=config,
            )
            latency = int((time.time() - start) * 1000)
            prompt_tokens     = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
            completion_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
            return ProviderResponse(
                provider=self.name(),
                model=model,
                content=response.text or "",
                finish_reason="stop",
                usage={
                    "prompt_tokens":     prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens":      prompt_tokens + completion_tokens,
                },
                latency_ms=latency,
                status=200,
            )
        except Exception as e:
            self._handle_error(e)

    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        if not self.client:
            raise ProviderAuthError("Gemini API key not configured")
        system_instruction, contents = self._convert_messages(messages)

        config_kwargs: Dict[str, Any] = {"request_options": types.RequestOptions(timeout=_TIMEOUT)}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if "temperature" in kwargs:
            config_kwargs["temperature"] = kwargs.pop("temperature")
        if "max_tokens" in kwargs:
            config_kwargs["max_output_tokens"] = kwargs.pop("max_tokens")

        config = types.GenerateContentConfig(**config_kwargs)

        try:
            stream = await self.client.aio.models.generate_content_stream(
                model=model, contents=contents, config=config,
            )
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            self._handle_error(e)

    async def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            await self.client.aio.models.generate_content(
                model=self.models[0],
                contents="ping",
                config=types.GenerateContentConfig(max_output_tokens=1),
            )
            return True
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False

    def supports_streaming(self) -> bool:
        return True

    def model_list(self) -> List[str]:
        return self.models

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        rates = {
            "gemini-1.5-pro":   (1.25, 5.0),
            "gemini-1.5-flash": (0.075, 0.3),
        }
        rate = rates.get(model, (0.0, 0.0))
        return (input_tokens * rate[0] / 1_000_000) + (output_tokens * rate[1] / 1_000_000)
