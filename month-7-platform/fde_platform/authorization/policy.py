"""Authorization policy contracts.

The policy model is deliberately small in Build 2. Later builds can replace the
policy implementation without changing callers or the identity contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from ..identity import RequestContext


class AuthorizationDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    context: RequestContext
    action: str
    resource: str
    resource_tenant_id: str
    required_scope: str | None = None
    required_roles: frozenset[str] = frozenset()


class Policy(Protocol):
    def evaluate(self, request: AuthorizationRequest) -> AuthorizationDecision: ...
