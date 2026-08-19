"""Human approval boundary for high-risk operations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol

from .risk import RiskTier


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    approval_id: str
    tenant_id: str
    subject: str
    action: str
    resource: str
    risk: RiskTier
    policy_version: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    approval_id: str
    status: ApprovalStatus
    decided_by: str | None = None
    decided_at: datetime | None = None


class ApprovalStore(Protocol):
    def put(self, request: ApprovalRequest) -> None: ...
    def get(self, approval_id: str) -> ApprovalRequest | None: ...
    def decide(self, decision: ApprovalDecision) -> None: ...


class InMemoryApprovalStore:
    """Deterministic reference store used by the policy boundary tests."""

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}
        self._decisions: dict[str, ApprovalDecision] = {}

    def put(self, request: ApprovalRequest) -> None:
        if request.approval_id in self._requests:
            raise ValueError("approval already exists")
        if request.expires_at <= request.created_at:
            raise ValueError("approval expiry must be after creation")
        self._requests[request.approval_id] = request

    def get(self, approval_id: str) -> ApprovalRequest | None:
        return self._requests.get(approval_id)

    def decide(self, decision: ApprovalDecision) -> None:
        request = self._requests.get(decision.approval_id)
        if request is None:
            raise KeyError("unknown approval")
        if decision.status not in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED}:
            raise ValueError("only terminal approval decisions may be recorded")
        if decision.decided_at is None or decision.decided_at.tzinfo is None:
            raise ValueError("decision timestamp must be timezone-aware")
        if decision.decided_at > request.expires_at:
            raise ValueError("approval has expired")
        if self._decisions.get(decision.approval_id) is not None:
            raise ValueError("approval is already decided")
        self._decisions[decision.approval_id] = decision


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
