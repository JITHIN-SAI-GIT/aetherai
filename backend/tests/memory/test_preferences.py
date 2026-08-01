import pytest
from app.memory.storage import MockStorage
from app.memory.preferences import PreferencesManager


@pytest.fixture
def mgr():
    return PreferencesManager(MockStorage())


@pytest.mark.asyncio
async def test_set_and_get(mgr):
    await mgr.set("u1", "language", "Python")
    val = await mgr.get("u1", "language")
    assert val == "Python"


@pytest.mark.asyncio
async def test_versioning(mgr):
    v1 = await mgr.set("u1", "language", "Python")
    v2 = await mgr.set("u1", "language", "Go")
    assert v2.version == 2
    assert v2.previous_value == "Python"


@pytest.mark.asyncio
async def test_no_duplicate_update(mgr):
    v1 = await mgr.set("u1", "language", "Python")
    v2 = await mgr.set("u1", "language", "Python")
    # Same value — should not increment version
    assert v2.version == v1.version


@pytest.mark.asyncio
async def test_delete_key(mgr):
    await mgr.set("u1", "editor", "vim")
    await mgr.delete_key("u1", "editor")
    val = await mgr.get("u1", "editor")
    assert val is None
