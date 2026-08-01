import logging
import os
from dataclasses import dataclass
from typing import Optional
from .exceptions import AuthenticationError
from .policies import POLICIES

logger = logging.getLogger("security.api_key_auth")

# Placeholder allow-list loaded from env (comma-separated)
_raw_keys = os.getenv("ALLOWED_API_KEYS", "test-key-local,demo-key")
_ALLOWED_KEYS = {k.strip() for k in _raw_keys.split(",") if k.strip()}


@dataclass
class AuthResult:
    authenticated: bool
    api_key_prefix: Optional[str] = None
    user_id: Optional[str] = None


class APIKeyAuth:
    """
    Placeholder API key middleware.
    Validates Authorization: Bearer <key> against an env-configured allow-list.
    When api_keys_enabled=False (default), all requests pass through.
    """

    def authenticate(self, authorization_header: Optional[str]) -> AuthResult:
        if not POLICIES.api_keys_enabled:
            # Auth disabled — permit all requests in development mode
            return AuthResult(authenticated=True, api_key_prefix="dev")

        if not authorization_header:
            logger.warning("Missing Authorization header")
            raise AuthenticationError("Missing Authorization header")

        scheme, _, key = authorization_header.partition(" ")
        if scheme.lower() != "bearer" or not key:
            raise AuthenticationError("Authorization header must be: Bearer <key>")

        key = key.strip()
        if key not in _ALLOWED_KEYS:
            logger.warning("Invalid API key", extra={"prefix": key[:8]})
            raise AuthenticationError("Invalid API key")

        return AuthResult(
            authenticated=True,
            api_key_prefix=key[:8],
            user_id=f"key:{key[:8]}",
        )
