"""Framework-neutral contracts for secure agent tool invocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class ToolCapability(str, Enum):
    """Explicit capabilities a tool may request."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXTERNAL_NETWORK = "external_network"
    SENSITIVE_DATA = "sensitive_data"


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Immutable allowlisted tool metadata; implementations stay outside the kernel."""

    name: str
    version: str
    description: str
    capabilities: frozenset[ToolCapability] = field(default_factory=frozenset)
    input_schema: Mapping[str, Any] = field(default_factory=dict)
    requires_approval: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("tool name is required")
        if not self.version.strip():
            raise ValueError("tool version is required")
        if not self.description.strip():
            raise ValueError("tool description is required")
        if not isinstance(self.capabilities, frozenset):
            raise TypeError("capabilities must be a frozenset")


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A single invocation explicitly bound to tenant and request context."""

    tool_name: str
    arguments: Mapping[str, Any]
    tenant_id: str
    request_id: str
    idempotency_key: str
    capabilities: frozenset[ToolCapability] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        for value, label in (
            (self.tool_name, "tool_name"),
            (self.tenant_id, "tenant_id"),
            (self.request_id, "request_id"),
            (self.idempotency_key, "idempotency_key"),
        ):
            if not value.strip():
                raise ValueError(f"{label} is required")


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Bounded, explicit result envelope returned by a tool adapter."""

    success: bool
    output: Any = None
    error_code: str | None = None
    retryable: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.success and self.error_code is not None:
            raise ValueError("successful result cannot contain an error code")
        if not self.success and not self.error_code:
            raise ValueError("failed result requires an error code")
