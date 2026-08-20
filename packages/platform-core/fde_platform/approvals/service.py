"""In-memory approval service with quorum, expiry and delegation semantics.

Persistence adapters can implement the same lifecycle without changing callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    request_id: str
    tenant_id: str
    action: str
    required_approvers: frozenset[str]
    quorum: int = 1
    expires_at: datetime | None = None
    status: str = "pending"
    approved_by: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.tenant_id.strip() or not self.action.strip():
            raise ValueError("request_id, tenant_id and action are required")
        if self.quorum < 1 or self.quorum > len(self.required_approvers):
            raise ValueError("quorum must be within approver count")


class ApprovalService:
    def __init__(self, default_ttl_seconds: int = 900) -> None:
        if default_ttl_seconds <= 0:
            raise ValueError("default_ttl_seconds must be positive")
        self._ttl = default_ttl_seconds
        self._requests: dict[str, ApprovalRequest] = {}

    def create(self, request_id: str, tenant_id: str, action: str, approvers: set[str], quorum: int = 1) -> ApprovalRequest:
        if request_id in self._requests:
            raise ValueError("approval request already exists")
        request = ApprovalRequest(
            request_id=request_id,
            tenant_id=tenant_id,
            action=action,
            required_approvers=frozenset(approvers),
            quorum=quorum,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=self._ttl),
        )
        self._requests[request_id] = request
        return request

    def approve(self, request_id: str, principal: str) -> ApprovalRequest:
        current = self._requests[request_id]
        now = datetime.now(timezone.utc)
        if current.expires_at and now >= current.expires_at:
            expired = ApprovalRequest(**{**current.__dict__, "status": "expired"}) if hasattr(current, "__dict__") else ApprovalRequest(
                current.request_id, current.tenant_id, current.action, current.required_approvers,
                current.quorum, current.expires_at, "expired", current.approved_by,
            )
            self._requests[request_id] = expired
            raise PermissionError("approval request expired")
        if principal not in current.required_approvers:
            raise PermissionError("principal is not an approver")
        approved = current.approved_by | {principal}
        status = "approved" if len(approved) >= current.quorum else "pending"
        updated = ApprovalRequest(current.request_id, current.tenant_id, current.action, current.required_approvers, current.quorum, current.expires_at, status, frozenset(approved))
        self._requests[request_id] = updated
        return updated

    def get(self, request_id: str) -> ApprovalRequest:
        return self._requests[request_id]
