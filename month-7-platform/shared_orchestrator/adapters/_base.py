"""Shared adapter helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable

from domain_agent import DomainAgentResult
from schemas import Domain


def normalize_result(
    domain: Domain,
    result: Any,
    *,
    confidence: float = 1.0,
    requires_human_review: bool = False,
    audit_metadata: Dict[str, Any] | None = None,
) -> DomainAgentResult:
    """Wrap domain results in the platform envelope, including dataclass engines."""
    if hasattr(result, "model_dump"):
        payload = result.model_dump(mode="json")
    elif is_dataclass(result) and not isinstance(result, type):
        payload = asdict(result)
    elif isinstance(result, dict):
        payload = result
    else:
        raise TypeError(f"Unsupported domain result type: {type(result)!r}")

    metadata = dict(audit_metadata or {})
    metadata.setdefault("deployment_mode", "human_in_the_loop")
    metadata.setdefault("safety_policy", "v1")

    return DomainAgentResult(
        domain=domain,
        status="processed",
        result=payload,
        confidence=max(0.0, min(1.0, float(confidence))),
        requires_human_review=bool(requires_human_review),
        audit_metadata=metadata,
    )


def requires_review_from_steps(steps: Iterable[Any], *field_names: str) -> bool:
    """Return True when any step explicitly requires human/counsel approval."""
    for step in steps:
        if isinstance(step, dict):
            if any(bool(step.get(name)) for name in field_names):
                return True
        elif any(bool(getattr(step, name, False)) for name in field_names):
            return True
    return False


def has_manual_steps(steps: Iterable[Any], field_name: str = "is_automated") -> bool:
    """Return True when at least one workflow step is explicitly non-automated."""
    for step in steps:
        value = step.get(field_name) if isinstance(step, dict) else getattr(step, field_name, None)
        if value is False:
            return True
    return False
