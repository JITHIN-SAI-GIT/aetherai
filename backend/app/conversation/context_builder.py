import logging
from typing import Optional, Dict, Any
from .models import ConversationContext, ToneResult, StyleResult
from .persona import Persona, DEFAULT_PERSONA
from .tone import ToneManager
from .response_style import ResponseStyleSelector
from .clarification import ClarificationEngine
from .followup import FollowUpEngine
from .language_detector import LanguageDetector

logger = logging.getLogger("conversation.context_builder")


class ConversationContextBuilder:
    """
    Assembles the full ConversationContext from pipeline inputs and compiles
    a single system prompt that is injected into the LLM BEFORE generation.

    The compiled system prompt (stored in ConversationContext.persona_instructions)
    contains, in order:
        1. Persona core + user profile facts (name, language, project, goals …)
           — now includes language_hint for the detected script/language
        2. Tone instruction (empathetic / technical / roman_telugu …)
        3. Style / formatting hints for this intent
        4. Conversation summary (when available — long-term memory compression)
        5. Agent behavioural overlay (expertise layer only — not identity)

    Called at pipeline Stage 4.5, BEFORE the provider call.
    """

    def __init__(
        self,
        persona: Optional[Persona] = None,
        tone_manager: Optional[ToneManager] = None,
        style_selector: Optional[ResponseStyleSelector] = None,
        clarification_engine: Optional[ClarificationEngine] = None,
        followup_engine: Optional[FollowUpEngine] = None,
        language_detector: Optional[LanguageDetector] = None,
    ):
        self._persona = persona or DEFAULT_PERSONA
        self._tone_mgr = tone_manager or ToneManager()
        self._style_sel = style_selector or ResponseStyleSelector()
        self._clarity = clarification_engine or ClarificationEngine()
        self._followup = followup_engine or FollowUpEngine()
        self._lang_detector = language_detector or LanguageDetector()

    def build(
        self,
        intent: str,
        messages: list,
        user_profile: Optional[Dict[str, Any]] = None,
        response_content: str = "",
        intent_confidence: float = 1.0,
        agent_system_prompt: Optional[str] = None,
        conversation_summary: Optional[str] = None,
    ) -> ConversationContext:
        profile = user_profile or {}

        # ── Language detection (on last user message) ──────────────────────
        last_user_msg = self._get_last_user_message(messages)
        lang_detection = self._lang_detector.detect(last_user_msg)
        detected_language = lang_detection.language

        if detected_language != "english":
            logger.info(
                "Non-English language detected",
                extra={
                    "language": detected_language,
                    "confidence": lang_detection.confidence,
                    "matched": lang_detection.matched_words,
                },
            )

        # ── Tone (now includes last_user_message for empathy detection) ────
        writing_tone = profile.get("writing_tone")
        tone = self._tone_mgr.select(
            intent=intent,
            user_tone_preference=writing_tone,
            last_user_message=last_user_msg,
        )

        # If language is Roman Telugu, promote to roman_telugu tone
        if detected_language == "roman_telugu" and tone.tone not in ("technical", "empathetic"):
            from .models import ToneResult
            tone = ToneResult(
                tone="roman_telugu",
                system_hint=self._tone_mgr._get_hint("roman_telugu"),
                source="language_detection",
            )
        elif detected_language in ("mixed_te_en", "mixed_hi_en") and tone.tone == "friendly":
            from .models import ToneResult
            tone = ToneResult(
                tone="mixed_language",
                system_hint=self._tone_mgr._get_hint("mixed_language"),
                source="language_detection",
            )

        # ── Style ──────────────────────────────────────────────────────────
        style = self._style_sel.select(intent)

        # ── Clarification ──────────────────────────────────────────────────
        clarification = self._clarity.evaluate(intent, intent_confidence)

        # ── Follow-up (now language-aware) ────────────────────────────────
        follow_up = self._followup.evaluate(
            messages, intent, response_content, detected_language
        )

        # ── Compile full system prompt ─────────────────────────────────────
        lang_hint = lang_detection.system_hint()
        compiled_system_prompt = self._compile_system_prompt(
            profile=profile,
            tone=tone,
            style=style,
            agent_system_prompt=agent_system_prompt,
            conversation_summary=conversation_summary,
            language_hint=lang_hint,
        )

        ctx = ConversationContext(
            tone=tone,
            style=style,
            persona_instructions=compiled_system_prompt,
            clarification=clarification,
            follow_up=follow_up,
            enriched_content=response_content or None,
            metadata={
                "intent": intent,
                "confidence": intent_confidence,
                "detected_language": detected_language,
                "lang_confidence": lang_detection.confidence,
            },
        )

        logger.info("Conversation context built", extra={
            "intent": intent,
            "tone": tone.tone,
            "style": style.style,
            "language": detected_language,
            "has_name": bool(profile.get("name")),
            "has_lang_hint": bool(lang_hint),
            "has_agent_overlay": bool(agent_system_prompt),
            "has_summary": bool(conversation_summary),
            "system_prompt_len": len(compiled_system_prompt),
            "clarification_needed": clarification.needed,
            "followup_needed": follow_up.needed,
        })
        return ctx

    # ── Private helpers ────────────────────────────────────────────────────

    def _compile_system_prompt(
        self,
        profile: Dict[str, Any],
        tone: ToneResult,
        style: StyleResult,
        agent_system_prompt: Optional[str],
        conversation_summary: Optional[str],
        language_hint: str = "",
    ) -> str:
        """
        Compile a single system prompt string from all layers.
        Parts are joined with double newlines; empty/None parts are skipped.
        """
        parts = []

        # 1. Persona core + user profile + language hint
        parts.append(
            self._persona.system_instructions(
                user_profile=profile,
                language_hint=language_hint,
            )
        )

        # 2. Tone instruction
        parts.append(tone.system_hint)

        # 3. Formatting / style hints
        if style.formatting_hints:
            parts.append(" ".join(style.formatting_hints))

        # 4. Conversation summary — compressed long-term memory
        if conversation_summary:
            parts.append(
                f"Summary of the conversation so far:\n{conversation_summary}"
            )

        # 5. Agent behavioural overlay — expertise only
        if agent_system_prompt:
            parts.append(agent_system_prompt)

        return "\n\n".join(p.strip() for p in parts if p and p.strip())

    def _get_last_user_message(self, messages: list) -> str:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                return content if isinstance(content, str) else ""
        return ""
