"""FastAPI dependency for service API keys and OIDC bearer identities."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException

from security.auth import Identity, bearer_authenticator
from security.oidc import AuthenticationError
from .auth import require_api_key


def _oidc_enabled() -> bool:
    return bool(os.getenv("FDE_OIDC_ISSUER", "").strip() and os.getenv("FDE_OIDC_AUDIENCE", "").strip())


def require_api_or_oidc(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
) -> Identity | str:
    if authorization and authorization.lower().startswith("bearer ") and _oidc_enabled() and not x_api_key:
        try:
            return bearer_authenticator().authenticate(authorization.split(" ", 1)[1].strip())
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail="Invalid bearer token", headers={"WWW-Authenticate": "Bearer"}) from exc
    return require_api_key(authorization, x_api_key)


def require_scope(identity: Identity, scope: str) -> None:
    if scope not in identity.scopes:
        raise HTTPException(status_code=403, detail="Required scope is missing.")
