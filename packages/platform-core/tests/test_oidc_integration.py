from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from security.auth import Identity, OIDCAuthenticator, discover_jwks_url, require_identity
from security.oidc import AuthenticationError, OIDCSettings


def test_discovery_requires_https(monkeypatch):
    with pytest.raises(AuthenticationError, match="HTTPS"):
        discover_jwks_url("http://issuer.example")


def test_authenticator_uses_rotating_jwks_client(monkeypatch):
    settings = OIDCSettings(
        issuer="https://issuer.example",
        audience="fde-platform",
        jwks_url="https://issuer.example/keys",
        algorithms=("RS256",),
    )
    auth = OIDCAuthenticator(settings)
    assert auth._jwks is not None


def test_fastapi_bearer_dependency_rejects_missing_token():
    settings = OIDCSettings(
        issuer="https://issuer.example",
        audience="fde-platform",
        jwks_url="https://issuer.example/keys",
        algorithms=("RS256",),
    )
    app = FastAPI()
    auth = OIDCAuthenticator(settings)

    @app.get("/protected")
    async def protected(identity: Identity = Depends(require_identity(auth))):
        return {"sub": identity.subject}

    response = TestClient(app).get("/protected")
    assert response.status_code == 401


def test_identity_extracts_tenant_and_scopes():
    now = datetime.now(timezone.utc)
    settings = OIDCSettings(
        issuer="https://issuer.example",
        audience="fde-platform",
        jwks_url="https://issuer.example/keys",
        algorithms=("HS256",),
    )
    token = jwt.encode(
        {
            "iss": settings.issuer,
            "aud": settings.audience,
            "sub": "user-1",
            "tenant_id": "tenant-1",
            "scope": "agents:read agents:execute",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        "secret",
        algorithm="HS256",
    )

    auth = OIDCAuthenticator(settings)
    auth._jwks = type("StaticJWK", (), {"get_signing_key_from_jwt": lambda self, _: type("Key", (), {"key": "secret"})()})()
    identity = auth.authenticate(token)
    assert identity.subject == "user-1"
    assert identity.tenant_id == "tenant-1"
    assert identity.scopes == {"agents:read", "agents:execute"}
