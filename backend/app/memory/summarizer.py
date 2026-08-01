"""
ConversationSummarizer — real LLM-based compression (Fix 8).

When conversation exceeds SUMMARY_THRESHOLD user turns, calls the provider
chain (via ProviderManager) to produce a concise natural-language summary.
Falls back to a structured placeholder only if the LLM call fails.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from .models import ConversationSummary

logger = logging.getLogger("memory.summarizer")

# Trigger summarization after this many user turns in a session
SUMMARY_THRESHOLD = 15


class ConversationSummarizer:
    """
    LLM-backed conversation summarizer.
    Accepts an optional provider_manager for real summarization.
    Falls back gracefully if no manager is provided or LLM call fails.
    """

    def __init__(self, provider_manager=None):
        self._provider_manager = provider_manager

    def should_summarize(self, messages: List[Dict[str, Any]]) -> bool:
        user_turns = sum(1 for m in messages if m.get("role") == "user")
        return user_turns >= SUMMARY_THRESHOLD

    def summarize(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_id: str,
    ) -> ConversationSummary:
        """
        Synchronous wrapper — calls async _summarize_async via asyncio.
        Falls back to placeholder on any error.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In async context (FastAPI), schedule a coroutine safely
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self._summarize_async(messages, user_id, session_id),
                    )
                    return future.result(timeout=10)
            else:
                return loop.run_until_complete(
                    self._summarize_async(messages, user_id, session_id)
                )
        except Exception as e:
            logger.warning(f"LLM summarizer failed, using placeholder: {e}")
            return self._placeholder_summary(messages, user_id, session_id)

    async def summarize_async(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_id: str,
    ) -> ConversationSummary:
        """Async version — preferred when called from an async context."""
        return await self._summarize_async(messages, user_id, session_id)

    async def _summarize_async(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_id: str,
    ) -> ConversationSummary:
        user_turns = [m for m in messages if m.get("role") == "user"]
        count = len(user_turns)

        if self._provider_manager:
            try:
                # Build a summarization prompt from the conversation
                convo_text = "\n".join(
                    f"{m['role'].upper()}: {m.get('content','')}"
                    for m in messages
                    if m.get("role") in ("user", "assistant") and m.get("content")
                )
                summarize_messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a conversation summarizer. "
                            "Produce a concise 2-4 sentence summary of the conversation below, "
                            "capturing the main topics, key facts the user shared, and any "
                            "important context for a follow-up conversation. "
                            "Be factual, brief, and refer to the user in third person."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this conversation:\n\n{convo_text[-4000:]}",
                    },
                ]
                response = await self._provider_manager.generate(
                    messages=summarize_messages,
                    model="auto",
                    max_tokens=200,
                )
                summary_text = response.content.strip()
                logger.info(
                    "LLM summary generated",
                    extra={"user_id": user_id, "session_id": session_id, "turns": count},
                )
                return ConversationSummary(
                    user_id=user_id,
                    session_id=session_id,
                    summary=summary_text,
                    turn_range=(0, count),
                    message_count_compressed=count,
                )
            except Exception as e:
                logger.warning(f"LLM summary call failed: {e}")

        return self._placeholder_summary(messages, user_id, session_id)

    def _placeholder_summary(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_id: str,
    ) -> ConversationSummary:
        user_turns = [m for m in messages if m.get("role") == "user"]
        count = len(user_turns)
        topics = self._extract_topics(user_turns)
        summary_text = (
            f"The user had a {count}-turn conversation covering: {topics}. "
            "No further details are available."
        )
        return ConversationSummary(
            user_id=user_id,
            session_id=session_id,
            summary=summary_text,
            turn_range=(0, count),
            message_count_compressed=count,
        )

    def compress(
        self,
        messages: List[Dict[str, Any]],
        summary: ConversationSummary,
        keep_last: int = 6,
    ) -> List[Dict[str, Any]]:
        """Replace old messages with the summary, keeping the last N turns."""
        recent      = messages[-keep_last:]
        summary_msg = {"role": "system", "content": summary.summary}
        return [summary_msg] + recent

    def _extract_topics(self, user_turns: List[Dict[str, Any]]) -> str:
        all_text = " ".join(m.get("content", "") for m in user_turns[:5])
        words    = [w for w in all_text.split() if len(w) > 5]
        return ", ".join(set(words[:5])) or "general conversation"
