import pytest
from app.memory.storage import MockStorage
from app.memory.privacy import PrivacyManager
from app.memory.exceptions import MemoryPrivacyError


@pytest.fixture
def privacy():
    s = MockStorage()
    return PrivacyManager(s), s


@pytest.mark.asyncio
async def test_delete_requires_confirmation(privacy):
    mgr, storage = privacy
    with pytest.raises(MemoryPrivacyError):
        await mgr.delete_all("u1", confirmed=False)


@pytest.mark.asyncio
async def test_delete_all_with_confirmation(privacy):
    mgr, storage = privacy
    await storage.set("u1", "test_key", "value")
    await mgr.delete_all("u1", confirmed=True)
    exported = await storage.export("u1")
    assert exported == {}


@pytest.mark.asyncio
async def test_export_profile(privacy):
    mgr, storage = privacy
    await storage.set("u1", "__profile__", {"user_id": "u1", "preferred_language": "Python"})
    data = await mgr.export_profile("u1")
    assert data["user_id"] == "u1"
    assert data["profile"]["preferred_language"] == "Python"
