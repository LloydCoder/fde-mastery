"""Fail-closed authorization boundary for consequential agent actions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionRisk(str, Enum):
    READ = "read"
    LOW = "low"
    HIGH = "high"
    DESTRUCTIVE = "destructive"


@dataclass(frozen=True)
class ActionRequest:
    tenant_id: str
    actor_id: str
    action: str
    risk: ActionRisk
    approved: bool = False
    policy_version: str = "v1"


def authorize(request: ActionRequest) -> bool:
    """Return True only when an action satisfies explicit safety requirements."""
    if not request.tenant_id or not request.actor_id or not request.action:
        return False
    if request.risk in {ActionRisk.READ, ActionRisk.LOW}:
        return True
    return request.approved


def require_authorized(request: ActionRequest) -> None:
    if not authorize(request):
        raise PermissionError(
            f"Action '{request.action}' is blocked: explicit policy/HITL approval is required"
        )
