"""FastAPI dependencies that avoid loading identity-provider configuration for anonymous requests."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from .auth import bearer_authenticator
from .oidc import AuthenticationError


def require_bearer_from_env():
    async def dependency(request: Request):
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            return bearer_authenticator().authenticate(token.strip())
        except AuthenticationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    return dependency
