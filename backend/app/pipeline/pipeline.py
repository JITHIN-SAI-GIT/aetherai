import logging
import time
from .context import PipelineContext
from .metrics import track_stage
from .exceptions import PipelineError

logger = logging.getLogger("pipeline")

# Maximum messages sent to the LLM — keeps context tight & latency low.
# 16 messages = 8 back-and-forth turns (system prompt excluded from count).
MAX_MESSAGES_TO_LLM = 16

# Token budget for the final assembled prompt sent to any provider.
# Leaves generous headroom for the 450-token output cap while staying safely
# within Groq's context window and its 5s per-request timeout.
# Multilingual (Hindi / Telugu / CJK) text is ~2-4x more token-dense than
# English for the same character count, so a naive message-count cap is
# insufficient — this budget catches those cases.
MAX_PROMPT_TOKENS = 3500


def _estimate_tokens(text: str) -> int:
    """
    Lightweight token estimator without a tokenizer dependency.
    Uses character-to-token ratios that are empirically accurate to ±20%:
      - ASCII / Latin:   ~4 chars per token  (ratio = 0.25)
      - Non-ASCII (CJK, Devanagari, Arabic, etc.): ~1.5 chars per token (ratio ≈ 0.67)
    We detect non-ASCII dominance by checking if >30% of chars are non-ASCII.
    """
    if not text:
        return 0
    non_ascii = sum(1 for c in text if ord(c) > 127)
    ratio = 0.6 if non_ascii / max(len(text), 1) > 0.3 else 0.25
    return max(1, int(len(text) * ratio))


def _count_prompt_tokens(messages: list) -> int:
    """Estimate total token count for a list of messages."""
    total = 0
    for msg in messages:
        content = msg.get("content") or ""
        total += _estimate_tokens(content) + 4  # ~4 overhead tokens per message
    return total


def _trim_to_token_budget(messages: list, budget: int = MAX_PROMPT_TOKENS) -> list:
    """
    Progressively remove the *oldest non-system* messages until the estimated
    token count fits within `budget`. Always preserves:
      - The system message (index 0 if role=="system")
      - The final user message (index -1)
    """
    if _count_prompt_tokens(messages) <= budget:
        return messages

    has_system = messages and messages[0].get("role") == "system"
    system_part = [messages[0]] if has_system else []
    history     = list(messages[1:] if has_system else messages)

    while len(history) > 1 and _count_prompt_tokens(system_part + history) > budget:
        history.pop(0)  # remove oldest turn

    trimmed = system_part + history
    logger.info(
        "Token budget applied — trimmed conversation history",
        extra={
            "estimated_tokens": _count_prompt_tokens(trimmed),
            "budget": budget,
            "messages_kept": len(trimmed),
        },
    )
    return trimmed


def _slice_messages(messages: list, max_count: int = MAX_MESSAGES_TO_LLM) -> list:
    """
    Return at most `max_count` messages, always keeping the system message (if
    present at index 0) plus the most recent user/assistant turns.
    """
    if len(messages) <= max_count:
        return messages

    # Preserve system message + last (max_count - 1) conversation turns
    if messages and messages[0].get("role") == "system":
        system_msg  = messages[0]
        tail        = messages[-(max_count - 1):]
        sliced      = [system_msg] + tail
    else:
        sliced = messages[-max_count:]

    logger.info(
        "Message window applied",
        extra={"original": len(messages), "sliced": len(sliced), "max": max_count},
    )
    return sliced


class Pipeline:
    """
    Assembles and executes the ordered chain of pipeline stages.
    Stage order:
        1.    Intent Detection
        2.    Load Session Context (memory)
        3.    Search Decision
        3.5   Search Execution
        4.    Agent Routing
        4.5   Conversation Context Build
        4.6   System Prompt Injection
        4.7   Search Context Injection
        5.    Provider Call  (ProviderManager — circuit-breaker fallback chain)
        6.    Critic Review
        7.    Quality Review
        8.    Format Response
        8.5   Citation Appending
        9.    Memory Update
    """

    def __init__(
        self,
        intent_detector,
        context_loader,
        search_detector,
        search_executor,
        agent_manager,
        provider_manager,          # ProviderManager replaces provider_router + provider_call
        critic,
        conversation_manager,
        search_injector,
        formatter,
        citation_appender,
        memory_updater,
    ):
        self.intent_detector      = intent_detector
        self.context_loader       = context_loader
        self.search_detector      = search_detector
        self.search_executor      = search_executor
        self.agent_manager        = agent_manager
        self.provider_manager     = provider_manager
        self.critic               = critic
        self.conversation_manager = conversation_manager
        self.search_injector      = search_injector
        self.formatter            = formatter
        self.citation_appender    = citation_appender
        self.memory_updater       = memory_updater

    async def run(self, context: PipelineContext) -> PipelineContext:
        pipeline_start = time.perf_counter()

        # ── Stage 1: Intent Detection ─────────────────────────────────────
        with track_stage(context, "intent_detection"):
            context = self.intent_detector.detect(context)

        # ── Stage 2: Load Session Context ─────────────────────────────────
        with track_stage(context, "context_loading"):
            context = await self.context_loader.load(context)

        # ── Stage 3: Search Decision ──────────────────────────────────────
        with track_stage(context, "search_detection"):
            context = self.search_detector.detect(context)

        # ── Stage 3.5: Search Execution ───────────────────────────────────
        with track_stage(context, "search_execution"):
            try:
                context = await self.search_executor.execute(context)
            except Exception as e:
                context.errors.append(f"SearchExecutor error: {e}")
                logger.warning("SearchExecutor failed", extra={"error": str(e)})

        # ── Stage 4: Agent Routing ────────────────────────────────────────
        with track_stage(context, "agent_routing"):
            try:
                selection, agent_result = self.agent_manager.select(
                    intent=context.intent,
                    messages=context.messages,
                    user_profile=context.user_context.session_metadata.get("profile", {}),
                    search_required=context.search_decision.required,
                    conversation_summary=context.user_context.conversation_summary,
                    user_preferences=context.user_context.preferences,
                )
                context.agent_selection       = selection
                context.agent_system_prompt   = agent_result.system_prompt
            except Exception as e:
                context.errors.append(f"AgentManager error: {e}")

        # ── Stage 4.5: Conversation Context Build ─────────────────────────
        with track_stage(context, "conversation_context"):
            try:
                context.conversation_context = self.conversation_manager.build_context(
                    intent=context.intent,
                    messages=context.messages,
                    user_profile=context.user_context.session_metadata.get("profile", {}),
                    response_content="",
                    agent_system_prompt=context.agent_system_prompt,
                    conversation_summary=context.user_context.conversation_summary,
                )
            except Exception as e:
                context.errors.append(f"ConversationContext error: {e}")
                logger.warning("ConversationContext build failed", extra={"error": str(e)})

        # ── Stage 4.6: System Prompt Injection ────────────────────────────
        with track_stage(context, "system_prompt_injection"):
            if context.conversation_context:
                system_prompt = context.conversation_context.persona_instructions
                if system_prompt:
                    if context.messages and context.messages[0].get("role") == "system":
                        existing = context.messages[0].get("content") or ""
                        context.messages[0]["content"] = (
                            system_prompt + ("\n\n---\n\n" + existing if existing.strip() else "")
                        )
                    else:
                        context.messages.insert(0, {"role": "system", "content": system_prompt})
                    logger.info(
                        "System prompt injected",
                        extra={"request_id": context.request_id, "prompt_length": len(system_prompt)},
                    )

        # ── Stage 4.7: Search Context Injection ───────────────────────────
        with track_stage(context, "search_injection"):
            try:
                context = self.search_injector.inject(context)
            except Exception as e:
                context.errors.append(f"SearchInjector error: {e}")
                logger.warning("SearchInjector failed", extra={"error": str(e)})

        # ── Stage 5: Provider Call (with circuit-breaker fallback) ─────────
        with track_stage(context, "provider_call"):
            try:
                # Select best model from manager (first available provider)
                provider_name, model = self.provider_manager.select_model(context.model)
                context.selected_provider = provider_name
                context.model             = model

                logger.info(
                    "Calling provider via ProviderManager",
                    extra={
                        "request_id": context.request_id,
                        "provider":   provider_name,
                        "model":      model,
                    },
                )

                # Apply message window slicing then token-budget trimming.
                # Step 1: cap by message count (fast O(n) operation)
                llm_messages = _slice_messages(context.messages)
                # Step 2: cap by estimated token count — catches multilingual
                # (Hindi/Telugu/CJK) conversations where character-dense scripts
                # produce far more tokens than an equivalent English history.
                llm_messages = _trim_to_token_budget(llm_messages)

                logger.info(
                    "Final prompt assembled",
                    extra={
                        "request_id": context.request_id,
                        "messages": len(llm_messages),
                        "estimated_tokens": _count_prompt_tokens(llm_messages),
                    },
                )

                if context.stream:
                    context.provider_response = self.provider_manager.stream(
                        messages=llm_messages,
                        model=model,
                        max_tokens=context.max_tokens,
                    )
                else:
                    context.provider_response = await self.provider_manager.generate(
                        messages=llm_messages,
                        model=model,
                        max_tokens=context.max_tokens,
                    )

                    logger.info(
                        "Provider responded",
                        extra={
                            "request_id":  context.request_id,
                            "provider":    context.provider_response.provider,
                            "latency_ms":  context.provider_response.latency_ms,
                            "model":       context.provider_response.model,
                        },
                    )

            except Exception as e:
                context.errors.append(f"Provider error: {e}")
                context.provider_response = None
                context.degraded          = True
                logger.error(
                    "All providers failed",
                    extra={"request_id": context.request_id, "error": str(e)},
                )

        # ── Stage 6: Critic Review ────────────────────────────────────────
        with track_stage(context, "critic_review"):
            if not context.stream:
                context = self.critic.review(context)

        # ── Stage 7: Quality Review ───────────────────────────────────────
        with track_stage(context, "quality_review"):
            if not context.stream:
                try:
                    if context.provider_response and context.conversation_context:
                        final_content, quality = self.conversation_manager.review_and_format(
                            context.provider_response.content,
                            context.conversation_context,
                        )
                        context.provider_response.content = final_content
                        context.quality_result            = quality
                except Exception as e:
                    context.errors.append(f"QualityReview error: {e}")

        # ── Stage 8: Format Response ──────────────────────────────────────
        with track_stage(context, "formatting"):
            if not context.stream:
                context = self.formatter.format(context)

        # ── Stage 8.5: Citation Appending ─────────────────────────────────
        with track_stage(context, "citation_appending"):
            if not context.stream:
                try:
                    context = self.citation_appender.append(context)
                except Exception as e:
                    context.errors.append(f"CitationAppender error: {e}")
                    logger.warning("CitationAppender failed", extra={"error": str(e)})

        # ── Stage 9: Memory Update ────────────────────────────────────────
        with track_stage(context, "memory_update"):
            if not context.stream:
                context = await self.memory_updater.update(context)

        # ── Record total pipeline duration ────────────────────────────────
        context.timings["total_pipeline"] = round(
            (time.perf_counter() - pipeline_start) * 1000, 3
        )

        logger.info(
            "Pipeline complete",
            extra={
                "request_id": context.request_id,
                "intent":     context.intent,
                "provider":   context.selected_provider,
                "degraded":   context.degraded,
                "timings_ms": context.timings,
            },
        )
        return context
