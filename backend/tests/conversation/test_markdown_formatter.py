from app.conversation.markdown_formatter import MarkdownFormatter
from app.conversation.models import StyleResult


fmt = MarkdownFormatter()
coding_style = StyleResult(style="coding", use_markdown=True)


def test_fixes_unclosed_code_block():
    content = "Here is code:\n```python\nprint(\'hello\')"
    result = fmt.format(content, coding_style)
    assert result.count("```") % 2 == 0


def test_collapses_excessive_newlines():
    content = "Line one\n\n\n\n\nLine two"
    result = fmt.format(content, coding_style)
    assert "\n\n\n" not in result


def test_strips_trailing_whitespace():
    content = "Hello   \nWorld   "
    result = fmt.format(content, coding_style)
    for line in result.splitlines():
        assert line == line.rstrip()


def test_no_modification_needed():
    content = "This is a clean response with no issues."
    result = fmt.format(content, coding_style)
    assert result == content.strip()
