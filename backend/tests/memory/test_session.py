import time
from app.memory.session import SessionMemory


def test_add_and_retrieve():
    session = SessionMemory(max_turns=10, ttl_seconds=3600)
    session.add_message("s1", {"role": "user", "content": "Hi"})
    msgs = session.get_messages("s1")
    assert len(msgs) == 1
    assert msgs[0]["content"] == "Hi"


def test_max_turns_pruning():
    session = SessionMemory(max_turns=3, ttl_seconds=3600)
    for i in range(5):
        session.add_message("s1", {"role": "user", "content": str(i)})
    msgs = session.get_messages("s1")
    assert len(msgs) == 3
    assert msgs[0]["content"] == "2"  # oldest kept


def test_clear_session():
    session = SessionMemory()
    session.add_message("s1", {"role": "user", "content": "test"})
    session.clear("s1")
    assert session.get_messages("s1") == []


def test_expired_session_returns_empty():
    session = SessionMemory(max_turns=10, ttl_seconds=0)
    session.add_message("s1", {"role": "user", "content": "hi"})
    time.sleep(0.01)
    assert session.get_messages("s1") == []
