"""FastAPI-ready OIDC authentication using issuer discovery and JWKS rotation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping

import jwt
import requests
from fastapi import HTTPException, Request as FastAPIRequest, status
from jwt import PyJWKClient

from .oidc import AuthenticationError, OIDCSettings


@dataclass(frozen=True)
class Identity:
    subject: str
    issuer: str
    audience: str | tuple[str, ...]
    claims: Mapping[str, Any]

    @property
    def tenant_id(self) -> str | None:
        value = self.claims.get("tenant_id") or self.claims.get("tenant")
        return str(value) if value is not None else None

    @property
    def scopes(self) -> frozenset[str]:
        raw = self.claims.get("scope", "")
        if isinstance(raw, str):
            return frozenset(raw.split())
        if isinstance(raw, (list, tuple, set)):
            return frozenset(str(item) for item in raw)
        return frozenset()


def _https_url(url: str, label: str) -> str:
    if not url.lower().startswith("https://"):
        raise AuthenticationError(f"{label} must use HTTPS")
    return url


@lru_cache(maxsize=16)
def discover_jwks_url(issuer: str) -> str:
    """Resolve JWKS endpoint from OIDC discovery metadata."""
    issuer = issuer.rstrip("/")
    discovery_url = _https_url(f"{issuer}/.well-known/openid-configuration", "OIDC discovery URL")
    try:
        response = requests.get(
            discovery_url,
            headers={"Accept": "application/json", "User-Agent": "fde-mastery/1.0"},
            timeout=5,
        )
        response.raise_for_status()
        metadata = response.json()
    except requests.RequestException as exc:
        raise AuthenticationError("Unable to load OIDC discovery metadata") from exc
    if not isinstance(metadata, dict):
        raise AuthenticationError("OIDC discovery metadata is invalid")
    jwks_url = metadata.get("jwks_uri")
    if not isinstance(jwks_url, str) or not jwks_url:
        raise AuthenticationError("OIDC discovery metadata does not contain jwks_uri")
    return _https_url(jwks_url, "JWKS URL")


class OIDCAuthenticator:
    """Authenticate bearer tokens against an OIDC provider's rotating JWKS."""

    def __init__(self, settings: OIDCSettings):
        self.settings = settings
        jwks_url = settings.jwks_url or discover_jwks_url(settings.issuer)
        self._jwks = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=300, max_cached_keys=16)

    def authenticate(self, token: str) -> Identity:
        if not token:
            raise AuthenticationError("Bearer token is required")
        try:
            signing_key = self._jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self.settings.algorithms),
                audience=self.settings.audience,
                issuer=self.settings.issuer,
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid bearer token") from exc
        return Identity(
            subject=str(claims["sub"]),
            issuer=str(claims["iss"]),
            audience=claims["aud"],
            claims=claims,
        )


def bearer_authenticator(settings: OIDCSettings | None = None) -> OIDCAuthenticator:
    return OIDCAuthenticator(settings or OIDCSettings.from_env())


def require_identity(authenticator: OIDCAuthenticator):
    """Return a FastAPI dependency that authenticates an Authorization bearer token."""
    async def dependency(request: FastAPIRequest) -> Identity:
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer authentication required")
        try:
            return authenticator.authenticate(token.strip())
        except AuthenticationError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc

    return dependency
