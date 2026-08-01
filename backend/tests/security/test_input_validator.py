import pytest
from app.security.input_validator import InputValidator
from app.security.exceptions import InputValidationError


val = InputValidator()


def test_valid_payload_passes():
    payload = {"messages": [{"role": "user", "content": "Hello!"}], "model": "gpt-4"}
    val.validate(payload)  # should not raise


def test_rejects_too_many_messages():
    msgs = [{"role": "user", "content": "hi"}] * 60
    with pytest.raises(InputValidationError) as exc:
        val.validate({"messages": msgs})
    assert "Too many messages" in exc.value.reason


def test_rejects_oversized_message():
    payload = {"messages": [{"role": "user", "content": "x" * 40000}]}
    with pytest.raises(InputValidationError) as exc:
        val.validate(payload)
    assert "too long" in exc.value.reason


def test_rejects_control_characters():
    payload = {"messages": [{"role": "user", "content": "Hello\x00World"}]}
    with pytest.raises(InputValidationError) as exc:
        val.validate(payload)
    assert "control characters" in exc.value.reason


def test_rejects_deeply_nested_payload():
    deep = {"a": {"b": {"c": {"d": {"e": {"f": "too deep"}}}}}}
    payload = {"messages": [], "meta": deep}
    with pytest.raises(InputValidationError):
        val.validate(payload)
