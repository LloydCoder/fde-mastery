"""Domain plugin contracts and promotion metadata.

The contract is intentionally framework/provider neutral. Domain implementations
may be legacy compatibility adapters or native engines, but every promoted
domain must expose the same operational surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


_ALLOWED_LIFECYCLE_STAGES = frozenset({"discovery", "pilot", "production", "retired"})
_ALLOWED_RISK_LEVELS = frozenset({"low", "medium", "high", "critical"})


@dataclass(frozen=True, slots=True)
class DomainDescriptor:
    """Machine-readable contract for a production FDE domain."""

    domain_id: str
    display_name: str
    version: str
    capabilities: Tuple[str, ...] = ()
    lifecycle_stage: str = "pilot"
    risk_level: str = "medium"
    human_approval_required: bool = True
    evaluation_suite: str = ""
    representative_dataset: str = ""
    source: str = ""

    def validate(self) -> None:
        """Fail closed when a domain descriptor is incomplete or unsafe."""
        if not self.domain_id or self.domain_id != self.domain_id.strip():
            raise ValueError("domain_id must be a non-empty canonical identifier")
        if not self.display_name.strip():
            raise ValueError("display_name is required")
        if not self.version.strip():
            raise ValueError("version is required")
        if self.lifecycle_stage not in _ALLOWED_LIFECYCLE_STAGES:
            raise ValueError(f"unsupported lifecycle_stage: {self.lifecycle_stage}")
        if self.risk_level not in _ALLOWED_RISK_LEVELS:
            raise ValueError(f"unsupported risk_level: {self.risk_level}")
        if not self.capabilities:
            raise ValueError("at least one domain capability is required")
        if not self.evaluation_suite.strip():
            raise ValueError("evaluation_suite is required")
        if not self.representative_dataset.strip():
            raise ValueError("representative_dataset is required")
        if self.risk_level in {"high", "critical"} and not self.human_approval_required:
            raise ValueError("high/critical risk domains must require human approval")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "domain_id": self.domain_id,
            "display_name": self.display_name,
            "version": self.version,
            "capabilities": list(self.capabilities),
            "lifecycle_stage": self.lifecycle_stage,
            "risk_level": self.risk_level,
            "human_approval_required": self.human_approval_required,
            "evaluation_suite": self.evaluation_suite,
            "representative_dataset": self.representative_dataset,
            "source": self.source,
        }
