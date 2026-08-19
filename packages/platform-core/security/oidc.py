"""OIDC/JWT validation primitives for enterprise authentication.

The module validates JWT claims and issuer/audience configuration. Signature
verification is delegated to PyJWT/JWK support when configured; no token is
trusted merely because its payload can be decoded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

import jwt


class AuthenticationError(ValueError):
    """Raised when a bearer token cannot be authenticated."""


@dataclass(frozen=True)
class OIDCSettings:
    issuer: str
    audience: str
    jwks_url: str | None = None
    algorithms: tuple[str, ...] = ("RS256",)

    @classmethod
    def from_env(cls) -> "OIDCSettings":
        issuer = os.getenv("FDE_OIDC_ISSUER", "").strip()
        audience = os.getenv("FDE_OIDC_AUDIENCE", "").strip()
        jwks_url = os.getenv("FDE_OIDC_JWKS_URL", "").strip() or None
        algorithms = tuple(x.strip() for x in os.getenv("FDE_OIDC_ALGORITHMS", "RS256").split(",") if x.strip())
        if not issuer or not audience:
            raise AuthenticationError("OIDC issuer and audience are required")
        if not algorithms:
            raise AuthenticationError("At least one JWT algorithm is required")
        return cls(issuer=issuer, audience=audience, jwks_url=jwks_url, algorithms=algorithms)


def validate_claims(payload: Dict[str, Any], settings: OIDCSettings) -> Dict[str, Any]:
    """Validate issuer/audience/subject and return a normalized claims copy."""
    if payload.get("iss") != settings.issuer:
        raise AuthenticationError("Invalid token issuer")
    audience = payload.get("aud")
    if isinstance(audience, list):
        valid_audience = settings.audience in audience
    else:
        valid_audience = audience == settings.audience
    if not valid_audience:
        raise AuthenticationError("Invalid token audience")
    if not payload.get("sub"):
        raise AuthenticationError("Token subject is required")
    return dict(payload)


def decode_and_validate(token: str, *, key: Any, settings: OIDCSettings) -> Dict[str, Any]:
    """Cryptographically verify and validate a JWT using an explicit trusted key."""
    if not token or not token.strip():
        raise AuthenticationError("Bearer token is required")
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=list(settings.algorithms),
            audience=settings.audience,
            issuer=settings.issuer,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid bearer token") from exc
    return validate_claims(payload, settings)
