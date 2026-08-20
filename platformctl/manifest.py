"""Machine-readable enterprise platform capability manifest."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    boundary: str
    description: str


CAPABILITIES: tuple[Capability, ...] = (
    Capability("identity", "identity", "Principal, tenant, environment and request context."),
    Capability("control-plane", "control_plane", "Versioned agent, tool, model and policy registries."),
    Capability("runtime", "runtime", "Bounded agent execution, cancellation and checkpoints."),
    Capability("workflow", "workflow", "Durable execution, recovery, replay and leased tasks."),
    Capability("worker", "data_plane", "Crash-safe leased worker execution outside the API process."),
    Capability("policy", "trust", "Independent fail-closed policy decisions and risk gates."),
    Capability("approvals", "trust", "Quorum and expiry controls for high-impact actions."),
    Capability("sandbox", "trust", "Explicit workload isolation policy for custom/untrusted agents."),
    Capability("tools", "tools", "Capability-scoped, tenant-bound tool execution."),
    Capability("models", "models", "Versioned model registry, policy gates and fallback."),
    Capability("events", "events", "Transactional outbox and consumer idempotency."),
    Capability("protocols", "protocols", "Authorization-aware MCP and A2A interoperability contracts."),
    Capability("evaluation", "evaluation", "Golden datasets, scoring and promotion gates."),
    Capability("lineage", "operations", "Evidence-only decision lineage without chain-of-thought capture."),
    Capability("finops", "operations", "Tenant-aware token, tool and compute cost accounting."),
    Capability("incidents", "operations", "AI incident detection, containment and remediation lifecycle."),
    Capability("deployment", "deployment", "Shared, isolated and dedicated deployment profiles with residency."),
    Capability("observability", "observability", "Bounded telemetry and tenant-scoped operational signals."),
)


def manifest() -> dict[str, object]:
    """Return a stable, serialization-ready capability manifest."""
    return {
        "schema_version": "2.0",
        "platform_version": "1.12.0",
        "capabilities": [
            {"name": capability.name, "boundary": capability.boundary, "description": capability.description}
            for capability in CAPABILITIES
        ],
    }
