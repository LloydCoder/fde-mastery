"""Contract tests for the enterprise disaster-recovery policy."""

from __future__ import annotations

import json
from pathlib import Path


POLICY = Path(__file__).resolve().parents[1] / "deployment" / "dr-policy.json"


def test_dr_policy_is_valid_and_fail_closed() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))

    assert policy["schema_version"] == "1.0"
    assert policy["default_tier"] in policy["tiers"]
    assert policy["tiers"]["standard"]["rpo_minutes"] > 0
    assert policy["tiers"]["business"]["rto_minutes"] > 0
    assert policy["tiers"]["critical"]["rpo_minutes"] <= policy["tiers"]["business"]["rpo_minutes"]

    required = set(policy["required_controls"])
    assert {
        "encrypted_backup",
        "restore_verification",
        "writer_fencing",
        "tenant_residency_validation",
        "rls_validation",
        "policy_validation",
        "workflow_idempotency_validation",
        "sbom_validation",
        "release_provenance",
    } <= required

    invariants = policy["security_invariants"]
    assert all(invariants.values())


def test_recovery_order_fences_before_state_restore() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    order = policy["recovery_order"]

    assert order.index("fence_primary") < order.index("restore_database")
    assert order.index("verify_schema") < order.index("restore_queue_and_event_state")
    assert order.index("verify_tool_and_model_gates") < order.index("promote_recovery_region")
    assert order[-1] == "reconcile_state"
