"""OAuth 2.0 authorization-code + PKCE control-plane primitives."""
from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True, slots=True)
class OAuthAuthorizationRequest:
    state: str
    code_verifier: str
    code_challenge: str
    authorization_url: str


def create_pkce_request(*, authorization_endpoint: str, client_id: str, redirect_uri: str,
                        scopes: tuple[str, ...], extra_params: dict[str, str] | None = None) -> OAuthAuthorizationRequest:
    if not authorization_endpoint.startswith("https://"):
        raise ValueError("OAuth authorization endpoint must use HTTPS")
    if not client_id.strip() or not redirect_uri.startswith("https://"):
        raise ValueError("client_id and HTTPS redirect_uri are required")
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    state = secrets.token_urlsafe(32)
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    params.update(extra_params or {})
    return OAuthAuthorizationRequest(state, verifier, challenge, f"{authorization_endpoint}?{urlencode(params)}")


@dataclass(frozen=True, slots=True)
class OAuthTokenSet:
    access_token: str
    token_type: str
    expires_at_epoch: int
    refresh_token_reference: str | None = None
    scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.access_token.strip() or not self.token_type.strip():
            raise ValueError("OAuth token response is missing required fields")
        if self.expires_at_epoch <= 0:
            raise ValueError("OAuth token expiry must be an absolute epoch timestamp")
        if self.refresh_token_reference and any(x in self.refresh_token_reference.lower() for x in ("token=", "secret=")):
            raise ValueError("refresh token must be stored as an opaque managed-secret reference")
