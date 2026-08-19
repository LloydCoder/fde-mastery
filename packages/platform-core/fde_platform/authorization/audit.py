"""Tamper-evident authorization decision audit records."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json

from .engine import PolicyDecision


@dataclass(frozen=True, slots=True)
class AuthorizationAuditEvent:
    request_id: str
    tenant_id: str
    subject: str
    action: str
    resource: str
    decision: PolicyDecision
    occurred_at: datetime
    previous_digest: str = ""

    @property
    def digest(self) -> str:
        payload = {
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "subject": self.subject,
            "action": self.action,
            "resource": self.resource,
            "decision": self.decision.decision.value,
            "reason": self.decision.reason.value,
            "risk": int(self.decision.risk),
            "policy_version": self.decision.policy_version,
            "occurred_at": self.occurred_at.isoformat(),
            "previous_digest": self.previous_digest,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
