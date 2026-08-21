"""Build 15 contract tests for the enterprise integration plane."""
from __future__ import annotations

import hashlib
import hmac

import pytest

from integrations.http import OutboundHTTPClient, OutboundURLPolicy
from integrations.oauth import create_pkce_request
from integrations.plane import (
    AuthMethod,
    CredentialReference,
    IntegrationBinding,
    IntegrationDefinition,
    IntegrationRegistry,
)
from integrations.retry import TokenBucket, classify_retry, retry_after_seconds
from integrations.webhooks import ReplayGuard, verify_hmac_sha256, verify_timestamped_signature


def definition(auth: AuthMethod = AuthMethod.API_KEY) -> IntegrationDefinition:
    return IntegrationDefinition(
        provider="example",
        version="2026-01",
        auth_method=auth,
        capabilities=frozenset({"read", "write"}),
        allowed_hosts=frozenset({"api.example.com"}),
        webhook_events=frozenset({"created"}),
    )


def test_registry_is_tenant_and_environment_scoped() -> None:
    registry = IntegrationRegistry()
    binding = IntegrationBinding("tenant-a", "production", "crm-1", definition(), CredentialReference("crm-a"))
    registry.register(binding)
    assert registry.get("tenant-a", "production", "crm-1") == binding
    with pytest.raises(LookupError):
        registry.get("tenant-b", "production", "crm-1")
    with pytest.raises(LookupError):
        registry.get("tenant-a", "staging", "crm-1")


def test_authenticated_binding_requires_opaque_credential_reference() -> None:
    with pytest.raises(ValueError):
        IntegrationBinding("t", "production", "x", definition(), None)
    with pytest.raises(ValueError):
        CredentialReference("x?token=secret-value")
    anonymous = IntegrationBinding("t", "production", "x", definition(AuthMethod.NONE))
    assert anonymous.credential is None


def test_disabled_integrations_fail_closed() -> None:
    registry = IntegrationRegistry()
    registry.register(IntegrationBinding("t", "production", "x", definition(), CredentialReference("x")))
    registry.disable("t", "production", "x")
    with pytest.raises(PermissionError):
        registry.get("t", "production", "x")


def test_retry_respects_retry_after_and_attempt_budget() -> None:
    assert retry_after_seconds("2") == 2.0
    assert classify_retry(429, 1, retry_after="2").retry is True
    assert classify_retry(400, 1).retry is False
    assert classify_retry(503, 4).retry is False


def test_token_bucket_enforces_rate_limit() -> None:
    bucket = TokenBucket(capacity=2, refill_per_second=1)
    assert bucket.allow(0.0)
    assert bucket.allow(0.0)
    assert not bucket.allow(0.0)
    assert bucket.allow(1.0)


def test_webhook_signature_and_replay_protection() -> None:
    payload = b'{"event":"created"}'
    secret = "test-webhook-secret"
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_hmac_sha256(payload, f"sha256={digest}", secret)
    assert not verify_hmac_sha256(payload, "sha256=bad", secret)
    guard = ReplayGuard(ttl_seconds=10)
    assert guard.accept("delivery-1", now=100)
    assert not guard.accept("delivery-1", now=101)
    assert guard.accept("delivery-1", now=111)


def test_timestamped_webhook_signature_rejects_stale_payloads() -> None:
    payload = b"payload"
    secret = "secret"
    timestamp = 1000
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    assert verify_timestamped_signature(payload, f"t={timestamp},v1={signature}", secret, timestamp, now=1001)
    assert not verify_timestamped_signature(payload, f"t={timestamp},v1={signature}", secret, timestamp, now=1400)


def test_oauth_pkce_request_uses_s256_and_state() -> None:
    request = create_pkce_request(
        authorization_endpoint="https://login.example.com/oauth/authorize",
        client_id="client-1",
        redirect_uri="https://app.example.com/callback",
        scopes=("crm.read", "crm.write"),
    )
    assert request.state
    assert request.code_verifier
    assert request.code_challenge
    assert "code_challenge_method=S256" in request.authorization_url
    assert "state=" in request.authorization_url


def test_outbound_client_disables_redirects_and_validates_url() -> None:
    class Transport:
        def __init__(self) -> None:
            self.kwargs = None

        def request(self, method, url, **kwargs):
            self.kwargs = kwargs
            return {"ok": True}

    transport = Transport()
    client = OutboundHTTPClient(OutboundURLPolicy(frozenset({"api.example.com"}), allow_private_networks=True), transport)
    result = client.request("GET", "https://api.example.com/v1/health")
    assert result == {"ok": True}
    assert transport.kwargs["allow_redirects"] is False
    with pytest.raises(ValueError):
        client.request("GET", "http://api.example.com/v1/health")
    with pytest.raises(PermissionError):
        client.request("GET", "https://evil.example.com")
