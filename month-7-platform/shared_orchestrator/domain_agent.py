"""Standard contract for all FDE Mastery domain agents.

The domain projects were built independently and therefore expose slightly
 different method names and domain-specific Pydantic models. Month 7 should
 depend on a stable platform contract instead of knowing those implementation
 details.
"""

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable

from pydantic import BaseModel, Field

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
    """Stable interface consumed by the Month 7 orchestrator.

    Adapters implement this contract around the existing Month 1-6 agents.
    The platform therefore remains independent of domain-specific schemas and
    method names while preserving the existing domain implementations.
    """

    domain: Domain

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        """Evaluate a platform payload and return a normalized result."""
        ...

    def health(self) -> Dict[str, Any]:
        """Return lightweight agent readiness information."""
        ...

    def capabilities(self) -> Dict[str, Any]:
        """Describe the domain capabilities exposed through the platform."""
        ...
