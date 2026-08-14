"""Authentication helpers for the Month 7 API gateway.

Demo/portfolio implementation: API keys are supplied through environment
variables and never persisted in the client registry. Production deployments
should replace this with a managed identity provider or secret manager.
"""

import hmac
import os
from typing import Optional

from fastapi import Header, HTTPException


def _keys_from_env(name: str) -> set[str]:
    raw = os.getenv(name, "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def _configured_keys() -> tuple[set[str], set[str]]:
    return _keys_from_env("FDE_API_KEYS"), _keys_from_env("FDE_ADMIN_API_KEYS")


def _extract_api_key(authorization: Optional[str], x_api_key: Optional[str]) -> Optional[str]:
    if x_api_key:
        return x_api_key.strip()
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value.strip():
            return value.strip()
    return None


def require_api_key(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
) -> str:
    """Require a valid application API key using constant-time comparison."""
    key = _extract_api_key(authorization, x_api_key)
    regular_keys, _ = _configured_keys()
    if not key or not any(hmac.compare_digest(key, valid) for valid in regular_keys):
        raise HTTPException(status_code=401, detail="Authentication required.")
    return key


def require_admin_api_key(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
) -> str:
    """Require a dedicated administrator API key."""
    key = _extract_api_key(authorization, x_api_key)
    _, admin_keys = _configured_keys()
    if not key or not any(hmac.compare_digest(key, valid) for valid in admin_keys):
        raise HTTPException(status_code=403, detail="Administrator authorization required.")
    return key
