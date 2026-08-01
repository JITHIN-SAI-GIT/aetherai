import re
import logging
from .models import StyleResult

logger = logging.getLogger("conversation.markdown_formatter")

_EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")


class MarkdownFormatter:
    """
    Post-processes response content to fix and normalise markdown.
    Never over-formats — only corrects clearly broken structures.
    """

    def format(self, content: str, style: StyleResult) -> str:
        if not content:
            return content

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
