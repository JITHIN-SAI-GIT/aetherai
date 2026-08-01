from typing import List
from .exceptions import ProviderAuthError

class KeyRotator:
    def __init__(self, keys: List[str]):
        if not keys:
            self.keys = []
        else:
            self.keys = keys
        self.current_index = 0
        self.disabled_keys = set()

    def get_key(self) -> str:
        if not self.keys:
            return ""
        
        attempts = 0
        while attempts < len(self.keys):
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            if key not in self.disabled_keys:
                return key
            attempts += 1
        raise ProviderAuthError("No valid API keys available.")

    def disable_key(self, key: str):
        if key in self.keys:
            self.disabled_keys.add(key)
            
    def reset_key(self, key: str):
        if key in self.disabled_keys:
            self.disabled_keys.remove(key)
