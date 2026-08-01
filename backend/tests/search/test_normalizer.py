from app.search.normalizer import QueryNormalizer

norm = QueryNormalizer()


def test_lowercase():
    assert norm.normalize("Hello WORLD") == "hello world"


def test_strip_punctuation():
    result = norm.normalize("Hello, World!!")
    assert "," not in result
    assert "!" not in result


def test_collapse_spaces():
    assert norm.normalize("a   b   c") == "a b c"


def test_same_cache_key_for_reordered_tokens():
    k1 = norm.cache_key("AI news latest")
    k2 = norm.cache_key("latest AI news")
    assert k1 == k2


def test_different_cache_key_for_different_queries():
    k1 = norm.cache_key("What is Python?")
    k2 = norm.cache_key("What is JavaScript?")
    assert k1 != k2
