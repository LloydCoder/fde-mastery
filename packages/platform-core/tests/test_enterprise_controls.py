from security.policy import evaluate_action
from security.redaction import redact
from security.service_auth import issue_service_token, verify_service_token
from persistence.audit_chain import chain_event, verify_chain
from persistence.idempotency import IdempotencyConflict, MemoryIdempotencyStore
from evaluation.drift import detect_drift


def test_service_token_is_short_lived_and_audience_bound():
    token = issue_service_token("router", "agent", "secret", ttl_seconds=30)
    identity = verify_service_token(token, secret="secret", audience="agent")
    assert identity.subject == "router"


def test_redaction_removes_sensitive_fields_and_tokens():
    value = redact({"api_key": "secret", "nested": "sk-test-1234567890123456"})
    assert value["api_key"] == "[REDACTED]"
    assert "sk-test" not in value["nested"]


def test_policy_blocks_high_impact_without_approval():
    decision = evaluate_action(action="account_freeze", confidence=0.80, severity="critical")
    assert not decision.allowed
    assert decision.requires_human_approval


def test_idempotency_rejects_key_reuse_with_different_request():
    store = MemoryIdempotencyStore()
    store.put("k", "a", {"ok": True})
    assert store.get("k", "a") == {"ok": True}
    try:
        store.get("k", "b")
    except IdempotencyConflict:
        pass
    else:
        raise AssertionError("expected idempotency conflict")


def test_audit_chain_detects_tampering():
    first = chain_event("1", {"action": "login"})
    second = chain_event("2", {"action": "triage"}, first.event_hash)
    assert verify_chain([first, second])

    # Simulate persisted event tampering: mutate the payload but retain its stored hash.
    tampered = second.__class__(
        event_id=second.event_id,
        payload={"action": "tampered"},
        previous_hash=second.previous_hash,
        event_hash=second.event_hash,
    )
    assert not verify_chain([first, tampered])


def test_drift_gate_detects_material_regression():
    result = detect_drift(99, 100, 80, 100)
    assert result.drifted
