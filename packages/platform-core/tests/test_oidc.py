from datetime import datetime, timedelta, timezone

import jwt
import pytest

from security.oidc import AuthenticationError, OIDCSettings, decode_and_validate


@pytest.fixture
def settings():
    return OIDCSettings(issuer="https://issuer.example", audience="fde-platform")


def make_token(settings, key="secret", **claims):
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.issuer,
        "aud": settings.audience,
        "sub": "user-123",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        **claims,
    }
    return jwt.encode(payload, key, algorithm="HS256")


def test_valid_token_is_accepted():
    settings = OIDCSettings(issuer="https://issuer.example", audience="fde-platform", algorithms=("HS256",))
    token = make_token(settings)
    claims = decode_and_validate(token, key="secret", settings=settings)
    assert claims["sub"] == "user-123"


def test_wrong_signature_is_rejected(settings):
    settings = OIDCSettings(issuer=settings.issuer, audience=settings.audience, algorithms=("HS256",))
    token = make_token(settings)
    with pytest.raises(AuthenticationError, match="Invalid bearer token"):
        decode_and_validate(token, key="wrong", settings=settings)


def test_wrong_audience_is_rejected(settings):
    settings = OIDCSettings(issuer=settings.issuer, audience=settings.audience, algorithms=("HS256",))
    token = make_token(settings, aud="other-service")
    with pytest.raises(AuthenticationError):
        decode_and_validate(token, key="secret", settings=settings)


def test_expired_token_is_rejected(settings):
    settings = OIDCSettings(issuer=settings.issuer, audience=settings.audience, algorithms=("HS256",))
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"iss": settings.issuer, "aud": settings.audience, "sub": "u", "iat": now - timedelta(hours=1), "exp": now - timedelta(seconds=1)},
        "secret",
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError):
        decode_and_validate(token, key="secret", settings=settings)
