"""Execution context shared by future workflow and agent runtimes."""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Request-scoped context that can cross process boundaries safely."""

    request_id: str
    tenant_id: str
    environment: str = "development"
    trace_id: str | None = None
    deadline_ms: int | None = None
    attributes: Mapping[str, str] = None

    def __post_init__(self) -> None:
        if self.attributes is None:
            object.__setattr__(self, "attributes", {})
