import os

base_path = r"c:\Users\jithin sai\OneDrive\Desktop\finalbot\backend"

directories = ["app/conversation", "tests/conversation"]

files = {

# ── EXCEPTIONS ───────────────────────────────────────────────────────────────
"app/conversation/exceptions.py": '''class ConversationError(Exception):
    pass

class QualityError(ConversationError):
    def __init__(self, issue: str):
        self.issue = issue
        super().__init__(f"Quality issue: {issue}")

class ClarificationError(ConversationError):
    pass
''',

# ── MODELS ───────────────────────────────────────────────────────────────────
"app/conversation/models.py": '''from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ToneResult(BaseModel):
    tone: str
    system_hint: str
    source: str = "auto"  # "user_preference" | "intent" | "default"


class StyleResult(BaseModel):
    style: str
    formatting_hints: List[str] = Field(default_factory=list)
    code_expected: bool = False
    use_markdown: bool = True


class QualityResult(BaseModel):
    passed: bool = True
    issues: List[str] = Field(default_factory=list)
    corrected_content: Optional[str] = None
    corrections_applied: int = 0


class FollowUpResult(BaseModel):
    needed: bool = False
    question: Optional[str] = None
    reason: Optional[str] = None


class ClarificationResult(BaseModel):
    needed: bool = False
    question: Optional[str] = None
    confidence: float = 1.0


class ConversationContext(BaseModel):
    tone: ToneResult
    style: StyleResult
    persona_instructions: str
    clarification: ClarificationResult
    follow_up: FollowUpResult
    enriched_content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
''',

# ── POLICIES ─────────────────────────────────────────────────────────────────
"app/conversation/policies.py": '''from dataclasses import dataclass

@dataclass(frozen=True)
class ConversationPolicies:
    """Immutable global conversation rules. Config-driven in Phase 8+."""
    min_response_length: int = 10
    max_response_length: int = 4000
    clarification_confidence_threshold: float = 0.6
    max_repetition_phrase_len: int = 5
    repetition_window: int = 50        # words to scan for repeated n-grams
    keep_last_n_messages: int = 10
    banned_phrases: tuple = (
        "As an AI language model",
        "I cannot assist with",
        "I am unable to",
        "I don't have personal opinions",
        "As a large language model",
        "I'm just an AI",
    )
    default_tone: str = "professional"
    default_style: str = "general"


# Module-level singleton
POLICIES = ConversationPolicies()
''',

# ── EXAMPLES ─────────────────────────────────────────────────────────────────
"app/conversation/examples.py": '''"""
Few-shot style examples injected into persona context hints.
These are formatting hints, not actual prompts — no LLM call is made.
"""

STYLE_EXAMPLES: dict = {
    "coding": (
        "Respond with a clear explanation followed by a clean code block. "
        "Use syntax highlighting with the correct language tag. "
        "Explain each significant part briefly after the code."
    ),
    "math": (
        "Show working step-by-step. Use LaTeX notation where helpful. "
        "State the final answer clearly on its own line."
    ),
    "creative": (
        "Write in a flowing, engaging style. Avoid bullet points. "
        "Use vivid language and maintain a consistent tone throughout."
    ),
    "research": (
        "Organise by headings. Cite key facts. Use bullet points sparingly. "
        "Conclude with a concise summary paragraph."
    ),
    "explanation": (
        "Start with the core concept in one sentence. Build up with examples. "
        "Use analogies where helpful. End with a brief summary."
    ),
    "translation": (
        "Provide the translated text first, then a brief note on "
        "any idiomatic differences if relevant."
    ),
    "business": (
        "Use professional, concise language. Lead with the key point. "
        "Use bullet points for lists of items. Avoid jargon."
    ),
    "general": (
        "Be clear, friendly, and direct. Match the user's level of formality."
    ),
}
''',

# ── PERSONA ───────────────────────────────────────────────────────────────────
"app/conversation/persona.py": '''import os
from dataclasses import dataclass, field
from typing import List
from .policies import POLICIES


@dataclass
class Persona:
    """
    Config-driven global persona.
    Loaded from PERSONA_* environment variables; falls back to defaults.
    """
    name: str = "Aria"
    traits: List[str] = field(default_factory=lambda: [
        "professional", "helpful", "friendly", "direct",
        "technically accurate", "concise", "never repetitive",
    ])
    banned_phrases: tuple = POLICIES.banned_phrases

    def system_instructions(self) -> str:
        traits_str = ", ".join(self.traits)
        banned = "; ".join(f\'"{p}"\' for p in self.banned_phrases)
        return (
            f"You are {self.name}, an intelligent AI assistant. "
            f"Your personality traits: {traits_str}. "
            f"Never use these phrases: {banned}. "
            "Give concise, accurate, and helpful responses. "
            "Match the user\'s level of technicality. "
            "Never repeat yourself or pad responses."
        )


def load_persona() -> Persona:
    """Load persona from environment variables with sensible defaults."""
    name = os.getenv("PERSONA_NAME", "Aria")
    raw_traits = os.getenv("PERSONA_TRAITS", "")
    traits = [t.strip() for t in raw_traits.split(",") if t.strip()] or None
    p = Persona(name=name)
    if traits:
        p.traits = traits
    return p


# Module-level singleton — loaded once at startup
DEFAULT_PERSONA = load_persona()
''',

# ── TONE ─────────────────────────────────────────────────────────────────────
"app/conversation/tone.py": '''import logging
from typing import Optional, Dict
from .models import ToneResult
from .policies import POLICIES

logger = logging.getLogger("conversation.tone")

_TONE_HINTS: Dict[str, str] = {
    "professional": (
        "Respond in a professional, polished tone. "
        "Use precise language and avoid colloquialisms."
    ),
    "friendly": (
        "Respond in a warm, approachable tone. "
        "Feel free to use light, conversational language."
    ),
    "formal": (
        "Respond in a formal, structured tone. "
        "Avoid contractions and informal expressions."
    ),
    "technical": (
        "Respond with technical precision. "
        "Use domain-accurate terminology and assume technical familiarity."
    ),
    "casual": (
        "Keep it casual and conversational. "
        "Short sentences, plain language, friendly vibe."
    ),
}

_INTENT_TO_TONE: Dict[str, str] = {
    "coding":       "technical",
    "math":         "technical",
    "reasoning":    "professional",
    "creative":     "friendly",
    "translation":  "professional",
    "business":     "formal",
    "general":      "friendly",
    "chat":         "friendly",
}


class ToneManager:
    """
    Selects the appropriate tone for a response.
    Priority: user preference (Phase 6 profile) > intent mapping > default.
    """

    def select(
        self,
        intent: str = "general",
        user_tone_preference: Optional[str] = None,
    ) -> ToneResult:
        if user_tone_preference and user_tone_preference in _TONE_HINTS:
            tone = user_tone_preference
            source = "user_preference"
        elif intent in _INTENT_TO_TONE:
            tone = _INTENT_TO_TONE[intent]
            source = "intent"
        else:
            tone = POLICIES.default_tone
            source = "default"

        hint = _TONE_HINTS[tone]
        logger.info("Tone selected", extra={"tone": tone, "source": source})
        return ToneResult(tone=tone, system_hint=hint, source=source)
''',

# ── RESPONSE STYLE ────────────────────────────────────────────────────────────
"app/conversation/response_style.py": '''import logging
from typing import Dict
from .models import StyleResult
from .examples import STYLE_EXAMPLES
from .policies import POLICIES

logger = logging.getLogger("conversation.style")

_INTENT_TO_STYLE: Dict[str, str] = {
    "coding":                   "coding",
    "math":                     "math",
    "creative":                 "creative",
    "search_required":          "research",
    "reasoning":                "explanation",
    "translation":              "translation",
    "tool_request":             "coding",
    "clarification_required":   "general",
    "chat":                     "general",
    "general":                  "general",
}

_CODE_STYLES = {"coding", "math"}
_MARKDOWN_STYLES = {"coding", "math", "research", "explanation", "business"}


class ResponseStyleSelector:
    """
    Selects a response style based on Phase 4 intent.
    Provides formatting hints that flow into the context builder.
    """

    def select(self, intent: str) -> StyleResult:
        style = _INTENT_TO_STYLE.get(intent, POLICIES.default_style)
        hints_text = STYLE_EXAMPLES.get(style, STYLE_EXAMPLES["general"])
        formatting_hints = [hints_text]
        code_expected = style in _CODE_STYLES
        use_markdown = style in _MARKDOWN_STYLES

        logger.info("Style selected", extra={"intent": intent, "style": style})
        return StyleResult(
            style=style,
            formatting_hints=formatting_hints,
            code_expected=code_expected,
            use_markdown=use_markdown,
        )
''',

# ── CLARIFICATION ENGINE ──────────────────────────────────────────────────────
"app/conversation/clarification.py": '''import logging
from .models import ClarificationResult
from .policies import POLICIES

logger = logging.getLogger("conversation.clarification")

_CLARIFICATION_TEMPLATES = {
    "clarification_required": "Could you clarify what you mean by that?",
    "tool_request": "Which tool or function would you like me to use?",
    "general": "Could you provide a bit more detail so I can help you better?",
}


class ClarificationEngine:
    """
    Generates exactly one clarification question when confidence is low
    or intent is flagged as clarification_required.
    Never asks unnecessary questions.
    """

    def evaluate(
        self,
        intent: str,
        confidence: float = 1.0,
    ) -> ClarificationResult:
        needs_clarification = (
            intent == "clarification_required"
            or confidence < POLICIES.clarification_confidence_threshold
        )

        if not needs_clarification:
            return ClarificationResult(needed=False, confidence=confidence)

        question = _CLARIFICATION_TEMPLATES.get(intent, _CLARIFICATION_TEMPLATES["general"])
        logger.info(
            "Clarification triggered",
            extra={"intent": intent, "confidence": confidence},
        )
        return ClarificationResult(needed=True, question=question, confidence=confidence)
''',

# ── FOLLOW-UP ENGINE ─────────────────────────────────────────────────────────
"app/conversation/followup.py": '''import logging
from typing import List, Dict, Any
from .models import FollowUpResult

logger = logging.getLogger("conversation.followup")

# Intents that could benefit from a follow-up
_FOLLOWUP_INTENTS = {"coding", "creative", "research"}

# Keywords suggesting the user might need more
_AMBIGUITY_SIGNALS = [
    "something", "stuff", "thing", "it", "this", "that",
    "maybe", "perhaps", "not sure", "kind of",
]


class FollowUpEngine:
    """
    Determines whether a follow-up question should be asked.
    Only asks when information is missing, the request is ambiguous,
    or safety requires clarification.
    """

    def evaluate(
        self,
        messages: List[Dict[str, Any]],
        intent: str,
        response_content: str = "",
    ) -> FollowUpResult:
        last_user_msg = self._last_user_message(messages)

        # Very short user messages in high-detail intents are often ambiguous
        if intent in _FOLLOWUP_INTENTS and len(last_user_msg.split()) < 5:
            return FollowUpResult(
                needed=True,
                question="Could you share more details about what you need?",
                reason="user message too short for intent",
            )

        # Ambiguity signal detection
        lower = last_user_msg.lower()
        for signal in _AMBIGUITY_SIGNALS:
            if f" {signal} " in f" {lower} " and len(last_user_msg.split()) < 10:
                return FollowUpResult(
                    needed=True,
                    question="What specifically are you referring to?",
                    reason=f"ambiguity signal: '{signal}'",
                )

        return FollowUpResult(needed=False)

    def _last_user_message(self, messages: List[Dict[str, Any]]) -> str:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                return content if isinstance(content, str) else ""
        return ""
''',

# ── CONTEXT BUILDER ───────────────────────────────────────────────────────────
"app/conversation/context_builder.py": '''import logging
from typing import Optional, Dict, Any
from .models import ConversationContext
from .persona import Persona, DEFAULT_PERSONA
from .tone import ToneManager
from .response_style import ResponseStyleSelector
from .clarification import ClarificationEngine
from .followup import FollowUpEngine

logger = logging.getLogger("conversation.context_builder")


class ConversationContextBuilder:
    """
    Assembles the full ConversationContext from pipeline inputs.
    Reads Phase 4 intent, Phase 5 search results, Phase 6 user profile.
    No business logic lives here — pure assembly.
    """

    def __init__(
        self,
        persona: Optional[Persona] = None,
        tone_manager: Optional[ToneManager] = None,
        style_selector: Optional[ResponseStyleSelector] = None,
        clarification_engine: Optional[ClarificationEngine] = None,
        followup_engine: Optional[FollowUpEngine] = None,
    ):
        self._persona = persona or DEFAULT_PERSONA
        self._tone_mgr = tone_manager or ToneManager()
        self._style_sel = style_selector or ResponseStyleSelector()
        self._clarity = clarification_engine or ClarificationEngine()
        self._followup = followup_engine or FollowUpEngine()

    def build(
        self,
        intent: str,
        messages: list,
        user_profile: Optional[Dict[str, Any]] = None,
        response_content: str = "",
        intent_confidence: float = 1.0,
    ) -> ConversationContext:
        # Tone: user preference takes priority over intent mapping
        writing_tone = (user_profile or {}).get("writing_tone")
        tone = self._tone_mgr.select(intent=intent, user_tone_preference=writing_tone)

        # Style: purely intent-driven
        style = self._style_sel.select(intent)

        # Clarification: integrates Phase 4 intent + confidence threshold
        clarification = self._clarity.evaluate(intent, intent_confidence)

        # Follow-up: only for ambiguous short messages
        follow_up = self._followup.evaluate(messages, intent, response_content)

        ctx = ConversationContext(
            tone=tone,
            style=style,
            persona_instructions=self._persona.system_instructions(),
            clarification=clarification,
            follow_up=follow_up,
            enriched_content=response_content or None,
            metadata={"intent": intent, "confidence": intent_confidence},
        )
        logger.info("Conversation context built", extra={
            "intent": intent, "tone": tone.tone, "style": style.style,
            "clarification_needed": clarification.needed,
            "followup_needed": follow_up.needed,
        })
        return ctx
''',

# ── MARKDOWN FORMATTER ────────────────────────────────────────────────────────
"app/conversation/markdown_formatter.py": '''import re
import logging
from .models import StyleResult

logger = logging.getLogger("conversation.markdown_formatter")

_EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")
_UNCLOSED_CODE_BLOCK = re.compile(r"```[\w]*\n(?!.*```)", re.DOTALL)


class MarkdownFormatter:
    """
    Post-processes response content to fix and normalise markdown.
    Never over-formats — only corrects clearly broken structures.
    """

    def format(self, content: str, style: StyleResult) -> str:
        if not content:
            return content

        original = content
        corrections = 0

        # Fix unclosed code blocks
        open_count = content.count("```")
        if open_count % 2 != 0:
            content = content + "\n```"
            corrections += 1
            logger.info("Fixed unclosed code block")

        # Collapse excessive blank lines (> 2 consecutive)
        cleaned = _EXCESSIVE_NEWLINES.sub("\n\n", content)
        if cleaned != content:
            content = cleaned
            corrections += 1

        # Strip trailing whitespace per line
        lines = [line.rstrip() for line in content.splitlines()]
        content = "\n".join(lines)

        if corrections:
            logger.info("Markdown corrections applied",
                        extra={"corrections": corrections})

        return content.strip()
''',

# ── QUALITY REVIEWER ─────────────────────────────────────────────────────────
"app/conversation/quality.py": '''import re
import logging
from typing import List
from .models import QualityResult, StyleResult
from .policies import POLICIES

logger = logging.getLogger("conversation.quality")


class QualityReviewer:
    """
    Validates every response before it reaches the user.
    Issues are corrected where possible, otherwise flagged.
    """

    def review(self, content: str, style: StyleResult) -> QualityResult:
        issues: List[str] = []
        corrected = content
        corrections = 0

        # Check empty
        if not content or not content.strip():
            issues.append("response is empty")
            corrected = "I wasn\'t able to generate a response. Please try again."
            corrections += 1
            return QualityResult(
                passed=False, issues=issues,
                corrected_content=corrected, corrections_applied=corrections,
            )

        # Check too short
        if len(content.strip()) < POLICIES.min_response_length:
            issues.append(f"response too short ({len(content.strip())} chars)")

        # Check too verbose
        if len(content.strip()) > POLICIES.max_response_length:
            corrected = content[:POLICIES.max_response_length] + "\n\n[Truncated for length]"
            issues.append("response too verbose — truncated")
            corrections += 1

        # Check banned phrases
        for phrase in POLICIES.banned_phrases:
            if phrase.lower() in (corrected or content).lower():
                corrected = (corrected or content).replace(phrase, "")
                issues.append(f"banned phrase removed: {phrase!r}")
                corrections += 1

        # Check repeated phrases (sliding n-gram window)
        repeated = self._find_repetition(corrected or content)
        if repeated:
            issues.append(f"repeated phrase detected: {repeated!r}")

        passed = len(issues) == 0
        logger.info("Quality review complete", extra={
            "passed": passed,
            "issues": len(issues),
            "corrections": corrections,
        })
        return QualityResult(
            passed=passed,
            issues=issues,
            corrected_content=corrected if corrections else None,
            corrections_applied=corrections,
        )

    def _find_repetition(self, text: str, n: int = 4) -> str:
        """Detect repeated n-grams within a rolling window."""
        words = text.lower().split()
        seen = set()
        for i in range(len(words) - n + 1):
            gram = tuple(words[i: i + n])
            if gram in seen:
                return " ".join(gram)
            seen.add(gram)
        return ""
''',

# ── METRICS ───────────────────────────────────────────────────────────────────
"app/conversation/metrics.py": '''import logging
from typing import Dict, Any

logger = logging.getLogger("conversation.metrics")


class ConversationMetrics:
    def __init__(self):
        self._total = 0
        self._clarifications = 0
        self._followups = 0
        self._quality_corrections = 0
        self._formatting_corrections = 0
        self._total_length = 0

    def record(
        self,
        response_length: int,
        clarification: bool = False,
        followup: bool = False,
        quality_corrections: int = 0,
        formatting_corrections: int = 0,
    ) -> None:
        self._total += 1
        self._total_length += response_length
        if clarification:
            self._clarifications += 1
        if followup:
            self._followups += 1
        self._quality_corrections += quality_corrections
        self._formatting_corrections += formatting_corrections

    def snapshot(self) -> Dict[str, Any]:
        avg_len = round(self._total_length / self._total, 1) if self._total else 0
        return {
            "total_responses": self._total,
            "average_response_length": avg_len,
            "clarification_rate": round(self._clarifications / max(self._total, 1), 4),
            "followup_rate": round(self._followups / max(self._total, 1), 4),
            "quality_corrections": self._quality_corrections,
            "formatting_corrections": self._formatting_corrections,
        }


conversation_metrics = ConversationMetrics()
''',

# ── CONVERSATION MANAGER ─────────────────────────────────────────────────────
"app/conversation/conversation_manager.py": '''import logging
from .context_builder import ConversationContextBuilder
from .markdown_formatter import MarkdownFormatter
from .quality import QualityReviewer
from .metrics import ConversationMetrics, conversation_metrics
from .models import ConversationContext, QualityResult
from .persona import DEFAULT_PERSONA

logger = logging.getLogger("conversation.manager")


class ConversationManager:
    """
    Single entry point for the entire conversation enrichment layer.
    Called from the Phase 4 pipeline after the critic stage.
    """

    def __init__(
        self,
        context_builder: ConversationContextBuilder = None,
        markdown_formatter: MarkdownFormatter = None,
        quality_reviewer: QualityReviewer = None,
        metrics: ConversationMetrics = None,
    ):
        self._builder = context_builder or ConversationContextBuilder()
        self._md_fmt = markdown_formatter or MarkdownFormatter()
        self._quality = quality_reviewer or QualityReviewer()
        self._metrics = metrics or conversation_metrics

    def build_context(
        self,
        intent: str,
        messages: list,
        user_profile: dict = None,
        response_content: str = "",
        intent_confidence: float = 1.0,
    ) -> ConversationContext:
        """Build the conversation context — called as pipeline stage 7."""
        return self._builder.build(
            intent=intent,
            messages=messages,
            user_profile=user_profile,
            response_content=response_content,
            intent_confidence=intent_confidence,
        )

    def review_and_format(
        self, content: str, conv_ctx: ConversationContext
    ) -> tuple:
        """
        Run quality review then markdown formatting.
        Returns (final_content, quality_result).
        Called as pipeline stage 8.
        """
        # Step 1: Quality review
        quality = self._quality.review(content, conv_ctx.style)
        reviewed = quality.corrected_content if quality.corrected_content else content

        # Step 2: Markdown format
        formatted = self._md_fmt.format(reviewed, conv_ctx.style)

        # Step 3: Metrics
        self._metrics.record(
            response_length=len(formatted),
            clarification=conv_ctx.clarification.needed,
            followup=conv_ctx.follow_up.needed,
            quality_corrections=quality.corrections_applied,
        )

        return formatted, quality
''',

# ── TESTS ─────────────────────────────────────────────────────────────────────
"tests/conversation/__init__.py": "",

"tests/conversation/test_persona.py": '''from app.conversation.persona import load_persona, DEFAULT_PERSONA
from app.conversation.policies import POLICIES


def test_persona_has_name():
    assert DEFAULT_PERSONA.name


def test_persona_system_instructions_excludes_banned_phrases():
    instructions = DEFAULT_PERSONA.system_instructions()
    for phrase in POLICIES.banned_phrases:
        assert phrase not in instructions, f"Banned phrase found: {phrase}"


def test_persona_instructions_contain_name():
    p = load_persona()
    assert p.name in p.system_instructions()
''',

"tests/conversation/test_tone.py": '''from app.conversation.tone import ToneManager


mgr = ToneManager()


def test_coding_intent_gives_technical_tone():
    result = mgr.select(intent="coding")
    assert result.tone == "technical"
    assert result.source == "intent"


def test_creative_intent_gives_friendly_tone():
    result = mgr.select(intent="creative")
    assert result.tone == "friendly"


def test_user_preference_overrides_intent():
    result = mgr.select(intent="coding", user_tone_preference="casual")
    assert result.tone == "casual"
    assert result.source == "user_preference"


def test_default_tone_on_unknown_intent():
    result = mgr.select(intent="unknown_intent_xyz")
    assert result.tone == "professional"
    assert result.source == "default"
''',

"tests/conversation/test_response_style.py": '''from app.conversation.response_style import ResponseStyleSelector


sel = ResponseStyleSelector()


def test_coding_intent_gives_coding_style():
    r = sel.select("coding")
    assert r.style == "coding"
    assert r.code_expected is True


def test_math_intent_uses_markdown():
    r = sel.select("math")
    assert r.use_markdown is True


def test_creative_intent_gives_creative_style():
    r = sel.select("creative")
    assert r.style == "creative"


def test_general_fallback():
    r = sel.select("chat")
    assert r.style == "general"
''',

"tests/conversation/test_clarification.py": '''from app.conversation.clarification import ClarificationEngine


eng = ClarificationEngine()


def test_no_clarification_for_high_confidence_intent():
    result = eng.evaluate("chat", confidence=1.0)
    assert result.needed is False


def test_clarification_for_low_confidence():
    result = eng.evaluate("general", confidence=0.3)
    assert result.needed is True
    assert result.question


def test_clarification_for_explicit_intent():
    result = eng.evaluate("clarification_required", confidence=1.0)
    assert result.needed is True
    assert "clarify" in result.question.lower()
''',

"tests/conversation/test_followup.py": '''from app.conversation.followup import FollowUpEngine


eng = FollowUpEngine()


def _msgs(content: str):
    return [{"role": "user", "content": content}]


def test_no_followup_for_detailed_message():
    msgs = _msgs("Can you explain how async generators work in Python with an example?")
    result = eng.evaluate(msgs, intent="coding")
    assert result.needed is False


def test_followup_for_short_coding_message():
    msgs = _msgs("Fix it")
    result = eng.evaluate(msgs, intent="coding")
    assert result.needed is True


def test_no_followup_for_general_chat():
    msgs = _msgs("Hello, how are you?")
    result = eng.evaluate(msgs, intent="chat")
    assert result.needed is False
''',

"tests/conversation/test_markdown_formatter.py": '''from app.conversation.markdown_formatter import MarkdownFormatter
from app.conversation.models import StyleResult


fmt = MarkdownFormatter()
coding_style = StyleResult(style="coding", use_markdown=True)


def test_fixes_unclosed_code_block():
    content = "Here is code:\\n```python\\nprint(\\'hello\\')"
    result = fmt.format(content, coding_style)
    assert result.count("```") % 2 == 0


def test_collapses_excessive_newlines():
    content = "Line one\\n\\n\\n\\n\\nLine two"
    result = fmt.format(content, coding_style)
    assert "\\n\\n\\n" not in result


def test_strips_trailing_whitespace():
    content = "Hello   \\nWorld   "
    result = fmt.format(content, coding_style)
    for line in result.splitlines():
        assert line == line.rstrip()


def test_no_modification_needed():
    content = "This is a clean response with no issues."
    result = fmt.format(content, coding_style)
    assert result == content.strip()
''',

"tests/conversation/test_quality.py": '''from app.conversation.quality import QualityReviewer
from app.conversation.models import StyleResult


rev = QualityReviewer()
general_style = StyleResult(style="general")


def test_passes_valid_response():
    result = rev.review("This is a perfectly valid response with enough content.", general_style)
    assert result.passed is True


def test_fails_empty_response():
    result = rev.review("", general_style)
    assert result.passed is False
    assert "empty" in result.issues[0]
    assert result.corrected_content


def test_removes_banned_phrase():
    result = rev.review("As an AI language model, I can help you.", general_style)
    assert result.corrections_applied >= 1
    assert "As an AI language model" not in (result.corrected_content or "")


def test_detects_repetition():
    # Repeat a 4-gram multiple times
    text = "this is a test " * 10
    result = rev.review(text, general_style)
    assert any("repeated" in issue for issue in result.issues)
''',

"tests/conversation/test_conversation_manager.py": '''from app.conversation.conversation_manager import ConversationManager


mgr = ConversationManager()


def test_build_context_returns_context():
    ctx = mgr.build_context(
        intent="coding",
        messages=[{"role": "user", "content": "Write a Python sort function"}],
        user_profile={"writing_tone": None},
        response_content="Here is a function...",
    )
    assert ctx.tone.tone == "technical"
    assert ctx.style.style == "coding"
    assert ctx.persona_instructions


def test_review_and_format_corrects_banned_phrase():
    from app.conversation.models import ConversationContext, ToneResult, StyleResult
    from app.conversation.models import ClarificationResult, FollowUpResult
    ctx = ConversationContext(
        tone=ToneResult(tone="professional", system_hint=""),
        style=StyleResult(style="general"),
        persona_instructions="",
        clarification=ClarificationResult(needed=False),
        follow_up=FollowUpResult(needed=False),
    )
    content = "As an AI language model, here is the answer."
    final, quality = mgr.review_and_format(content, ctx)
    assert "As an AI language model" not in final


def test_metrics_updated_after_review():
    ctx = mgr.build_context(intent="chat",
                             messages=[{"role": "user", "content": "Hi"}])
    mgr.review_and_format("Hello! How can I help you today?", ctx)
    snap = mgr._metrics.snapshot()
    assert snap["total_responses"] >= 1
''',
}

# ── Create directories + __init__.py ──────────────────────────────────────────
for d in directories:
    dir_path = os.path.join(base_path, d)
    os.makedirs(dir_path, exist_ok=True)
    parts = d.split("/")
    for i in range(1, len(parts) + 1):
        init_dir = os.path.join(base_path, *parts[:i])
        init_file = os.path.join(init_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "a").close()

# ── Write all files ────────────────────────────────────────────────────────────
for file_path, content in files.items():
    full_path = os.path.join(base_path, file_path)
    os.makedirs(os.path.dirname(full_path) or base_path, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Phase 7 skeleton generated successfully.")
