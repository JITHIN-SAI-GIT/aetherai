import pytest
from app.providers.key_rotation import KeyRotator
from app.providers.exceptions import ProviderAuthError

def test_key_rotation():
    rotator = KeyRotator(["key1", "key2"])
    assert rotator.get_key() == "key1"
    assert rotator.get_key() == "key2"
    assert rotator.get_key() == "key1"

def test_key_disable():
    rotator = KeyRotator(["key1", "key2"])
    rotator.disable_key("key1")
    assert rotator.get_key() == "key2"
    assert rotator.get_key() == "key2"
    
    rotator.reset_key("key1")
    assert rotator.get_key() == "key1"
    assert rotator.get_key() == "key2"

def test_all_keys_disabled():
    rotator = KeyRotator(["key1"])
    rotator.disable_key("key1")
    with pytest.raises(ProviderAuthError):
        rotator.get_key()
