"""Execution context shared by future workflow and agent runtimes."""

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Request-scoped context that can cross process boundaries safely."""

    request_id: str
    tenant_id: str
    environment: str = "development"
    trace_id: str | None = None
    deadline_ms: int | None = None
    attributes: Mapping[str, str] = field(default_factory=dict)
