"""Framework-neutral agent request/response contracts.

The contracts deliberately contain no FastAPI, database, model-provider, or
vendor-specific types. That keeps the platform kernel stable as adapters evolve.
"""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class AgentRequest:
    """Immutable input to an agent execution."""

    request_id: str
    tenant_id: str
    agent_id: str
    input: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AgentResult:
    """Normalized result returned by an agent execution."""

    request_id: str
    agent_id: str
    output: str
    status: str = "completed"
    metadata: Mapping[str, Any] = field(default_factory=dict)
