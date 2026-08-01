import pytest
from app.search.detector import SearchNecessityDetector
from app.search.models import SearchCategory


det = SearchNecessityDetector()


def test_search_not_required_for_static_query():
    d = det.detect("What is React?", intent="chat")
    assert d.required is False


def test_search_required_for_latest_news():
    d = det.detect("Latest AI news", intent="chat")
    assert d.required is True
    assert d.category == SearchCategory.NEWS


def test_search_required_by_intent():
    d = det.detect("anything at all", intent="search_required")
    assert d.required is True
    assert d.confidence == 1.0


def test_weather_category():
    d = det.detect("What is the weather in London?", intent="chat")
    assert d.required is True
    assert d.category == SearchCategory.WEATHER


def test_sports_score_trigger():
    d = det.detect("What is the score of the match today?", intent="chat")
    assert d.required is True
