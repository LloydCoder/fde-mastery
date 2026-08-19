"""Standard contract for all FDE Mastery domain agents."""

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable

from pydantic import BaseModel, Field

try:
    from ..schemas import Domain
except ImportError:
    from schemas import Domain


class DomainAgentResult(BaseModel):
    """Platform-level envelope returned by every domain agent adapter."""

    domain: Domain
    status: str = Field(default="processed")
    result: Dict[str, Any]
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_human_review: bool = False
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class DomainAgent(Protocol):
    """Stable interface consumed by the Month 7 orchestrator."""

    domain: Domain

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        ...

    def health(self) -> Dict[str, Any]:
        ...

    def capabilities(self) -> Dict[str, Any]:
        ...
