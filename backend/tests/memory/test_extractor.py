import pytest
from app.memory.extractor import FactExtractor
from app.memory.models import MemoryClassification


ext = FactExtractor()


def _msgs(content: str):
    return [{"role": "user", "content": content}]


def test_extracts_preferred_language():
    result = ext.extract(_msgs("I prefer Python for all my projects"), user_id="u1")
    keys = [i.key for i in result.items]
    assert "preferred_language" in keys


def test_extracts_current_project():
    result = ext.extract(_msgs("I'm working on a chatbot application"), user_id="u1")
    keys = [i.key for i in result.items]
    assert "current_project" in keys


def test_ignores_greetings():
    result = ext.extract(_msgs("Hello!"), user_id="u1")
    assert result.ignored_count == 1
    assert result.items == []


def test_ignores_small_talk():
    result = ext.extract(_msgs("Thanks, that's cool!"), user_id="u1")
    assert result.ignored_count >= 1


def test_extracts_name():
    result = ext.extract(_msgs("My name is Alice"), user_id="u1")
    keys = [i.key for i in result.items]
    assert "name" in keys


def test_skips_assistant_messages():
    msgs = [
        {"role": "assistant", "content": "I prefer using FastAPI"},
        {"role": "user", "content": "Hello"},
    ]
    result = ext.extract(msgs, user_id="u1")
    # Only user messages are scanned; "hello" is ignored
    assert result.total_scanned == 1
