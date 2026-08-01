from app.conversation.followup import FollowUpEngine


eng = FollowUpEngine()


def _msgs(content: str):
    return [{"role": "user", "content": content}]


def test_no_followup_for_detailed_message():
    msgs = _msgs("Can you explain how async generators work in Python with an example?")
    result = eng.evaluate(msgs, intent="coding")
    assert result.needed is False


def test_followup_for_short_coding_message():
    msgs = _msgs("Fix it")
    result = eng.evaluate(msgs, intent="coding")
    assert result.needed is True


def test_no_followup_for_general_chat():
    msgs = _msgs("Hello, how are you?")
    result = eng.evaluate(msgs, intent="chat")
    assert result.needed is False
