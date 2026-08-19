"""Authentication helpers for the Month 7 API gateway.

API keys are supplied through environment variables and never persisted in the
client registry. Production deployments should replace this with a managed
identity provider or secret manager.
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
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value.strip():
            return value.strip()
    return None


def _require_key(
    authorization: Optional[str],
    x_api_key: Optional[str],
    configured_keys: set[str],
    *,
    role: str,
) -> str:
    """Authenticate with RFC 9110-style 401/403 semantics.

    401 is used when no credentials were supplied. 403 is used when credentials
    were supplied but are not authorized for the requested resource.
    """
    key = _extract_api_key(authorization, x_api_key)
    if key is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not any(hmac.compare_digest(key, valid) for valid in configured_keys):
        raise HTTPException(status_code=403, detail=f"{role} authorization required.")
    return key


def require_api_key(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
) -> str:
    """Require a valid application API key using constant-time comparison."""
    regular_keys, _ = _configured_keys()
    return _require_key(authorization, x_api_key, regular_keys, role="Application")


def require_admin_api_key(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
) -> str:
    """Require a dedicated administrator API key."""
    _, admin_keys = _configured_keys()
    return _require_key(authorization, x_api_key, admin_keys, role="Administrator")
