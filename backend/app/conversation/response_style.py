import logging
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
