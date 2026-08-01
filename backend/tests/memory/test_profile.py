import pytest
from app.memory.storage import MockStorage
from app.memory.profile import ProfileManager


@pytest.fixture
def mgr():
    return ProfileManager(MockStorage())


@pytest.mark.asyncio
async def test_default_profile(mgr):
    profile = await mgr.load("new_user")
    assert profile.user_id == "new_user"
    assert profile.preferred_language is None


@pytest.mark.asyncio
async def test_update_profile(mgr):
    profile = await mgr.update("u1", preferred_language="Python", coding_style="functional")
    assert profile.preferred_language == "Python"
    assert profile.coding_style == "functional"


@pytest.mark.asyncio
async def test_profile_persists(mgr):
    await mgr.update("u1", preferred_framework="FastAPI")
    profile = await mgr.load("u1")
    assert profile.preferred_framework == "FastAPI"
