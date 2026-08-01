import time
import logging
from typing import List, Dict, Any, AsyncGenerator
import anthropic
from anthropic import AsyncAnthropic
from app.providers.models import ProviderResponse
from app.providers.exceptions import ProviderError, ProviderTimeoutError, ProviderRateLimitError, ProviderAuthError
from app.config.settings import get_settings

logger = logging.getLogger("provider.anthropic")

class AnthropicProvider:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.anthropic_api_key if hasattr(settings, 'anthropic_api_key') else None
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None
        self.models = ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]

    def name(self) -> str: 
        return "anthropic"

    def _handle_error(self, e: Exception):
        if isinstance(e, anthropic.RateLimitError):
            raise ProviderRateLimitError(str(e))
        elif isinstance(e, anthropic.AuthenticationError):
            raise ProviderAuthError(str(e))
        elif isinstance(e, (anthropic.APITimeoutError, anthropic.APIConnectionError)):
            raise ProviderTimeoutError(str(e))
        raise ProviderError(str(e))

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
        """Convert standard OpenAI-style messages to Anthropic style (extracts system prompt)."""
        system = ""
        anthropic_msgs = []
        for msg in messages:
            if msg.get("role") == "system":
                system += msg.get("content", "") + "\n"
            else:
                anthropic_msgs.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })
        return system.strip(), anthropic_msgs

    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse:
        if not self.client:
            raise ProviderAuthError("Anthropic API key not configured")
        
        system_prompt, anthropic_msgs = self._convert_messages(messages)
        start_time = time.time()
        
        # Default max_tokens if not provided
        if "max_tokens" not in kwargs:
            kwargs["max_tokens"] = 4096
            
        try:
            response = await self.client.messages.create(
                model=model,
                messages=anthropic_msgs,
                system=system_prompt if system_prompt else anthropic.NotGiven(),
                stream=False,
                **kwargs
            )
            latency = int((time.time() - start_time) * 1000)
            
            return ProviderResponse(
                provider=self.name(),
                model=model,
                content=response.content[0].text if response.content else "",
                finish_reason=response.stop_reason or "stop",
                usage={
                    "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                    "completion_tokens": response.usage.output_tokens if response.usage else 0,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
                },
                latency_ms=latency,
                status=200
            )
        except Exception as e:
            self._handle_error(e)

    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        if not self.client:
            raise ProviderAuthError("Anthropic API key not configured")
            
        system_prompt, anthropic_msgs = self._convert_messages(messages)
        
        if "max_tokens" not in kwargs:
            kwargs["max_tokens"] = 4096
            
        try:
            async with self.client.messages.stream(
                model=model,
                messages=anthropic_msgs,
                system=system_prompt if system_prompt else anthropic.NotGiven(),
                **kwargs
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            self._handle_error(e)

    async def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            # Send a tiny message to check if API is up
            await self.client.messages.create(
                model=self.models[0],
                messages=[{"role": "user", "content": "hello"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            print(f"[ANTHROPIC] internal health check error: {e}")
            return False

    def supports_streaming(self) -> bool:
        return True

    def model_list(self) -> List[str]: 
        return self.models

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        rates = {
            "claude-3-opus-20240229": (15.0, 75.0),
            "claude-3-sonnet-20240229": (3.0, 15.0),
            "claude-3-5-sonnet-20241022": (3.0, 15.0),
            "claude-3-haiku-20240307": (0.25, 1.25)
        }
        rate = rates.get(model, (0.0, 0.0))
        return (input_tokens * rate[0] / 1_000_000) + (output_tokens * rate[1] / 1_000_000)
