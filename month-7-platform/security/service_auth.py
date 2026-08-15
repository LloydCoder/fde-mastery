"""Short-lived service-to-service authentication primitives.

For deployments that provide mTLS at the mesh/ingress layer, the presented
service identity can be mapped to this contract. For environments without a
mesh, this module provides an HMAC-signed, short-lived token fallback.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass

import jwt


@dataclass(frozen=True)
class ServiceIdentity:
    subject: str
    audience: str
    expires_at: int


def issue_service_token(subject: str, audience: str, secret: str, ttl_seconds: int = 60) -> str:
    if not subject or not audience or not secret:
        raise ValueError("subject, audience and secret are required")
    if not 1 <= ttl_seconds <= 300:
        raise ValueError("service token TTL must be between 1 and 300 seconds")
    now = int(time.time())
    return jwt.encode({"sub": subject, "aud": audience, "iat": now, "exp": now + ttl_seconds}, secret, algorithm="HS256")


def verify_service_token(token: str, *, secret: str, audience: str) -> ServiceIdentity:
    if not secret:
        raise ValueError("service authentication secret is required")
    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"], audience=audience, options={"require": ["exp", "iat", "sub", "aud"]})
    except jwt.PyJWTError as exc:
        raise ValueError("invalid service token") from exc
    return ServiceIdentity(subject=str(claims["sub"]), audience=str(claims["aud"]), expires_at=int(claims["exp"]))


def verify_mtls_identity(subject: str, *, allowed_subjects: frozenset[str]) -> bool:
    """Validate a service identity already established by a terminating mTLS proxy."""
    return bool(subject) and subject in allowed_subjects
