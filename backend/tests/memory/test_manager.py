import pytest
from app.memory.manager import MemoryManager
from app.memory.storage import MockStorage
from app.memory.extractor import FactExtractor
from app.memory.summarizer import ConversationSummarizer
from app.memory.session import SessionMemory
from app.memory.profile import ProfileManager
from app.memory.preferences import PreferencesManager
from app.memory.cleanup import MemoryCleanup
from app.memory.privacy import PrivacyManager
from app.memory.metrics import MemoryMetrics


def make_manager() -> MemoryManager:
    storage = MockStorage()
    return MemoryManager(
        storage=storage,
        extractor=FactExtractor(),
        summarizer=ConversationSummarizer(),
        session=SessionMemory(),
        profile_mgr=ProfileManager(storage),
        prefs_mgr=PreferencesManager(storage),
        cleanup=MemoryCleanup(storage),
        privacy=PrivacyManager(storage),
        metrics=MemoryMetrics(),
    )


@pytest.mark.asyncio
async def test_load_returns_context():
    mgr = make_manager()
    ctx = await mgr.load("u1", "s1")
    assert "profile" in ctx
    assert "preferences" in ctx
    assert "session_messages" in ctx


@pytest.mark.asyncio
async def test_extract_and_save():
    mgr = make_manager()
    msgs = [{"role": "user", "content": "I prefer Python"}]
    result = await mgr.extract(msgs, "u1")
    await mgr.save("u1", result)
    metrics = mgr.get_metrics()
    assert metrics["facts_extracted"] >= 1
    assert metrics["save_count"] == 1


@pytest.mark.asyncio
async def test_clear_session():
    mgr = make_manager()
    mgr._session.add_message("s1", {"role": "user", "content": "hi"})
    await mgr.clear_session("s1")
    assert mgr._session.get_messages("s1") == []


@pytest.mark.asyncio
async def test_delete_requires_confirmation():
    import pytest
    from app.memory.exceptions import MemoryPrivacyError
    mgr = make_manager()
    with pytest.raises(MemoryPrivacyError):
        await mgr.delete("u1", confirmed=False)


@pytest.mark.asyncio
async def test_summarize_returns_none_below_threshold():
    mgr = make_manager()
    msgs = [{"role": "user", "content": "hi"}]
    result = await mgr.summarize(msgs, "u1", "s1")
    assert result is None
