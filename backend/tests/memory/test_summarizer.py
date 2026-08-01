from app.memory.summarizer import ConversationSummarizer, SUMMARY_THRESHOLD


summ = ConversationSummarizer()


def _make_messages(n: int):
    return [{"role": "user", "content": f"message {i}"} for i in range(n)]


def test_should_not_summarize_below_threshold():
    msgs = _make_messages(SUMMARY_THRESHOLD - 1)
    assert summ.should_summarize(msgs) is False


def test_should_summarize_at_threshold():
    msgs = _make_messages(SUMMARY_THRESHOLD)
    assert summ.should_summarize(msgs) is True


def test_summary_contains_turn_count():
    msgs = _make_messages(SUMMARY_THRESHOLD)
    summary = summ.summarize(msgs, "u1", "s1")
    assert str(SUMMARY_THRESHOLD) in summary.summary
    assert summary.message_count_compressed == SUMMARY_THRESHOLD


def test_compress_keeps_recent_messages():
    msgs = _make_messages(SUMMARY_THRESHOLD + 5)
    summary = summ.summarize(msgs, "u1", "s1")
    compressed = summ.compress(msgs, summary, keep_last=5)
    # First message is the summary system message
    assert compressed[0]["role"] == "system"
    assert len(compressed) == 6  # 1 summary + 5 recent
