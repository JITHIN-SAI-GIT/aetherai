from app.search.summarizer import Summarizer

summ = Summarizer()


def test_strips_html_from_title():
    raw = [{"title": "<b>Bold Title</b>", "snippet": "text", "url": "https://a.com"}]
    results = summ.summarize(raw)
    assert "<b>" not in results[0].title
    assert results[0].title == "Bold Title"


def test_strips_html_from_snippet():
    raw = [{"title": "T", "snippet": "<p>Para text</p>", "url": "https://b.com"}]
    results = summ.summarize(raw)
    assert "<p>" not in results[0].snippet


def test_uses_description_fallback():
    raw = [{"title": "T", "description": "Desc text", "url": "https://c.com"}]
    results = summ.summarize(raw)
    assert results[0].snippet == "Desc text"


def test_summary_truncated_to_200_chars():
    long_text = "x" * 500
    raw = [{"title": "T", "snippet": long_text, "url": "https://d.com"}]
    results = summ.summarize(raw)
    assert len(results[0].summary) == 200
