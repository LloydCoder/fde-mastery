"""Machine-readable platform capability manifest.

This module deliberately depends only on the standard library so the CLI can be
used before provider SDKs or infrastructure adapters are installed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    boundary: str
    description: str


CAPABILITIES: tuple[Capability, ...] = (
    Capability("identity", "identity", "Principal, tenant, environment and request context."),
    Capability("runtime", "runtime", "Bounded agent execution, cancellation and checkpoints."),
    Capability("workflow", "workflow", "Durable execution, recovery, replay and leased tasks."),
    Capability("policy", "authorization", "Fail-closed policy decisions and approvals."),
    Capability("tools", "tools", "Capability-scoped, tenant-bound tool execution."),
    Capability("models", "models", "Versioned model registry, policy gates and fallback."),
    Capability("events", "events", "Transactional outbox and consumer idempotency."),
    Capability("evaluation", "evaluation", "Golden datasets, scoring and promotion gates."),
    Capability("observability", "observability", "Bounded telemetry and tenant-scoped FinOps."),
    Capability("resilience", "deployment", "Residency, RPO/RTO and recovery controls."),
)


def manifest() -> dict[str, object]:
    """Return a stable, serialization-ready capability manifest."""
    return {
        "schema_version": "1.0",
        "platform_version": "1.11.0",
        "capabilities": [
            {
                "name": capability.name,
                "boundary": capability.boundary,
                "description": capability.description,
            }
            for capability in CAPABILITIES
        ],
    }
