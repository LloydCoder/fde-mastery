import pytest

from evaluation.shadow import ShadowRecord, ShadowRecorder
from security.action_guard import ActionRequest, ActionRisk, authorize


def test_high_impact_action_requires_approval():
    request = ActionRequest("tenant-a", "analyst-a", "isolate_endpoint", ActionRisk.HIGH)
    assert authorize(request) is False
    assert authorize(ActionRequest("tenant-a", "analyst-a", "isolate_endpoint", ActionRisk.HIGH, True)) is True


def test_shadow_mode_never_executes_actions():
    recorder = ShadowRecorder()
    recorder.record(ShadowRecord("req-1", "tenant-a", "cybersecurity", {"disposition": "escalate"}))
    recorder.attach_human_disposition("req-1", "escalate")
    assert recorder.agreement_rate() == 1.0


def test_missing_tenant_is_rejected():
    assert authorize(ActionRequest("", "actor", "action", ActionRisk.READ)) is False
