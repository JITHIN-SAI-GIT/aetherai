from app.conversation.conversation_manager import ConversationManager


mgr = ConversationManager()


def test_build_context_returns_context():
    ctx = mgr.build_context(
        intent="coding",
        messages=[{"role": "user", "content": "Write a Python sort function"}],
        user_profile={"writing_tone": None},
        response_content="Here is a function...",
    )
    assert ctx.tone.tone == "technical"
    assert ctx.style.style == "coding"
    assert ctx.persona_instructions


def test_review_and_format_corrects_banned_phrase():
    from app.conversation.models import ConversationContext, ToneResult, StyleResult
    from app.conversation.models import ClarificationResult, FollowUpResult
    ctx = ConversationContext(
        tone=ToneResult(tone="professional", system_hint=""),
        style=StyleResult(style="general"),
        persona_instructions="",
        clarification=ClarificationResult(needed=False),
        follow_up=FollowUpResult(needed=False),
    )
    content = "As an AI language model, here is the answer."
    final, quality = mgr.review_and_format(content, ctx)
    assert "As an AI language model" not in final


def test_metrics_updated_after_review():
    ctx = mgr.build_context(intent="chat",
                             messages=[{"role": "user", "content": "Hi"}])
    mgr.review_and_format("Hello! How can I help you today?", ctx)
    snap = mgr._metrics.snapshot()
    assert snap["total_responses"] >= 1
