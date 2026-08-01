import pytest
from app.security.secret_filter import SecretFilter, _shannon_entropy


sf = SecretFilter()


def test_clean_content_unchanged():
    content = "Here is a simple explanation of Python."
    result, count = sf.filter(content)
    assert result == content
    assert count == 0


def test_redacts_openai_key():
    content = "Use this key: sk-abcdefghijklmnopqrstuvwxyz123456"
    result, count = sf.filter(content)
    assert "sk-" not in result
    assert "[REDACTED]" in result
    assert count >= 1


def test_redacts_jwt():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    result, count = sf.filter(f"Token: {jwt}")
    assert jwt not in result
    assert count >= 1


def test_redacts_db_url():
    content = "Connect to postgresql://admin:secret123@db.example.com/mydb"
    result, count = sf.filter(content)
    assert "secret123" not in result
    assert count >= 1


def test_shannon_entropy_high_for_random():
    import string, random
    random_str = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    assert _shannon_entropy(random_str) > 4.0


def test_shannon_entropy_low_for_repeated():
    assert _shannon_entropy("aaaaaaaaaa") < 1.0
