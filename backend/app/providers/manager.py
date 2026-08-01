"""
ProviderManager — circuit-breaker-aware fallback orchestration.

Iterates providers in priority order (Groq-1 → Groq-2 → Gemini → OpenRouter).
Each provider has its own CircuitBreaker instance.
On failure:
  - Records the failure on that provider's breaker.
  - After `failure_threshold` consecutive failures → circuit opens (provider marked DOWN).
  - Moves to the next provider immediately.
On success:
  - Records success on the breaker (resets failure counter, marks UP).
After cooldown_seconds:
  - A DOWN provider transitions to HALF_OPEN and gets one retry.
  - Success → CLOSED (UP). Failure → OPEN again.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .models import ProviderResponse
from .circuit_breaker import CircuitBreaker, CircuitState
from .exceptions import (
    ProviderError, ProviderAuthError, CircuitBreakerOpenError,
    NoAvailableProviderError
)

logger = logging.getLogger("providers.manager")

# How many consecutive failures before a provider is marked DOWN
FAILURE_THRESHOLD = 3
# Seconds to wait before retrying a DOWN provider
COOLDOWN_SECONDS = 60
# Default max_tokens cap (Phase 6 — latency fix)
DEFAULT_MAX_TOKENS = 450


@dataclass
class ProviderEntry:
    """A provider instance paired with its own circuit breaker."""
    provider: Any           # Any object satisfying the Provider protocol
    breaker: CircuitBreaker = field(default_factory=lambda: CircuitBreaker(
        failure_threshold=FAILURE_THRESHOLD,
        cooldown_seconds=COOLDOWN_SECONDS,
    ))

    def name(self) -> str:
        return self.provider.name()


class ProviderManager:
    """
    Single public interface for the provider fallback chain.
    Called by the pipeline stage instead of ProviderRouter+provider call.
    """

    def __init__(self, entries: List[ProviderEntry]):
        self._entries = entries

    # ── Public API ─────────────────────────────────────────────────────────

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ProviderResponse:
        """
        Try providers in priority order.  Skip if circuit is OPEN.
        Returns the first successful ProviderResponse.
        Raises NoAvailableProviderError if all providers fail or are DOWN.
        """
        effective_max_tokens = max_tokens or DEFAULT_MAX_TOKENS
        last_error: Optional[Exception] = None

        for entry in self._entries:
            if not entry.breaker.can_execute():
                logger.warning(
                    "Provider circuit OPEN — skipping",
                    extra={"provider": entry.name(), "state": entry.breaker.state.value},
                )
                continue

            try:
                logger.info(
                    "Attempting provider",
                    extra={"provider": entry.name(), "model": model},
                )
                # Resolve supported model name for this provider
                provider_model = model
                if model not in entry.provider.model_list():
                    provider_model = entry.provider.model_list()[0]

                response = await entry.provider.generate(
                    messages=messages,
                    model=provider_model,
                    max_tokens=effective_max_tokens,
                    **kwargs,
                )
                entry.breaker.record_success()
                logger.info(
                    "Provider call succeeded",
                    extra={
                        "provider": entry.name(),
                        "latency_ms": response.latency_ms,
                        "circuit_state": entry.breaker.state.value,
                    },
                )
                return response

            except ProviderAuthError as e:
                # Auth errors are permanent — open circuit immediately
                logger.error(
                    "Provider auth error — opening circuit",
                    extra={"provider": entry.name(), "error": str(e)},
                )
                # Force threshold failures so circuit opens
                for _ in range(FAILURE_THRESHOLD):
                    entry.breaker.record_failure()
                last_error = e
                continue

            except Exception as e:
                entry.breaker.record_failure()
                logger.warning(
                    "Provider call failed — trying next",
                    extra={
                        "provider": entry.name(),
                        "error": str(e),
                        "failure_count": entry.breaker.failures,
                        "circuit_state": entry.breaker.state.value,
                    },
                )
                last_error = e
                continue

        raise NoAvailableProviderError(
            f"All providers exhausted. Last error: {last_error}"
        )

    def stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        """
        Return an async generator that streams from the first available provider.
        Uses circuit-breaker logic + buffer-then-passthrough to prevent garbled
        output when a provider fails mid-stream.

        Strategy:
          - Buffer the first BUFFER_TOKENS tokens internally before yielding any
            to the client.
          - If the provider raises during buffering → discard buffer, try next
            provider cleanly (client never sees partial tokens from a failed attempt).
          - Once buffering succeeds → flush buffer then switch to direct pass-through.
        """
        effective_max_tokens = max_tokens or DEFAULT_MAX_TOKENS
        # Number of tokens to buffer before committing to a provider.
        # 15 tokens ≈ 60-100ms at Groq speed — imperceptible latency,
        # but enough to catch early failures before anything is shown.
        BUFFER_TOKENS = 15

        async def _inner():
            last_error = None
            for entry in self._entries:
                if not entry.breaker.can_execute():
                    logger.warning(
                        "Provider circuit OPEN (stream) — skipping",
                        extra={"provider": entry.name()},
                    )
                    continue

                # Resolve supported model name for this provider
                provider_model = model
                if model not in entry.provider.model_list():
                    provider_model = entry.provider.model_list()[0]

                logger.info("Streaming from provider", extra={"provider": entry.name()})

                # ── Phase 1: Buffer BUFFER_TOKENS tokens before yielding ──────
                # If the provider fails during this phase, nothing has been sent
                # to the client, so we can safely try the next provider.
                buffer: List[str] = []
                buffering_failed = False
                provider_gen = entry.provider.stream(
                    messages=messages,
                    model=provider_model,
                    max_tokens=effective_max_tokens,
                    **kwargs,
                )
                try:
                    async for chunk in provider_gen:
                        buffer.append(chunk)
                        if len(buffer) >= BUFFER_TOKENS:
                            break  # buffering phase complete — commit to this provider
                except ProviderAuthError as e:
                    for _ in range(FAILURE_THRESHOLD):
                        entry.breaker.record_failure()
                    logger.warning(
                        "Provider auth failure during buffer phase — trying next",
                        extra={"provider": entry.name(), "error": str(e)},
                    )
                    last_error = e
                    buffering_failed = True
                except Exception as e:
                    entry.breaker.record_failure()
                    logger.warning(
                        "Provider failed during buffer phase — trying next (client saw 0 tokens)",
                        extra={"provider": entry.name(), "error": str(e)},
                    )
                    last_error = e
                    buffering_failed = True

                if buffering_failed:
                    continue  # clean retry — client has seen nothing from this provider

                # ── Phase 2: Flush buffer then pass-through ───────────────────
                # We've committed to this provider. Yield buffered tokens first,
                # then stream the rest directly. Any exception here is caught by
                # sse_stream_generator's outer try/except and emits a clean error chunk.
                for buffered_chunk in buffer:
                    yield buffered_chunk

                try:
                    async for chunk in provider_gen:
                        yield chunk
                    entry.breaker.record_success()
                    return
                except ProviderAuthError as e:
                    for _ in range(FAILURE_THRESHOLD):
                        entry.breaker.record_failure()
                    last_error = e
                    # Re-raise so sse_stream_generator shows error chunk
                    raise NoAvailableProviderError(
                        f"Provider {entry.name()} auth failed mid-stream: {e}"
                    )
                except Exception as e:
                    entry.breaker.record_failure()
                    last_error = e
                    raise NoAvailableProviderError(
                        f"Provider {entry.name()} failed mid-stream after committing: {e}"
                    )

            raise NoAvailableProviderError(
                f"All providers exhausted for streaming. Last error: {last_error}"
            )

        return _inner()

    def select_model(self, requested_model: str) -> tuple[str, str]:
        """
        Return (provider_name, model_name) for the first available provider
        that can serve the requested model, or fall back to the first
        available provider's default model.
        """
        for entry in self._entries:
            if not entry.breaker.can_execute():
                continue
            if requested_model == "auto" or requested_model not in entry.provider.model_list():
                return entry.name(), entry.provider.model_list()[0]
            return entry.name(), requested_model
        # All down — return first provider's default anyway (will fail in generate)
        first = self._entries[0]
        return first.name(), first.provider.model_list()[0]

    def provider_statuses(self) -> List[Dict[str, Any]]:
        """Health summary for all providers (used by /health and /internal/metrics)."""
        return [
            {
                "provider": e.name(),
                "circuit_state": e.breaker.state.value,
                "failures": e.breaker.failures,
                "last_failure_time": e.breaker.last_failure_time,
            }
            for e in self._entries
        ]
