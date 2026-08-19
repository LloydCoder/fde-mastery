"""Framework-neutral contracts for enterprise model invocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence

from ..identity import RequestContext


class ModelCapability(str, Enum):
    CHAT = "chat"
    STRUCTURED_OUTPUT = "structured_output"
    VISION = "vision"
    TOOL_CALLING = "tool_calling"


class DataClass(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ModelErrorCode(str, Enum):
    MODEL_NOT_FOUND = "model_not_found"
    CAPABILITY_DENIED = "capability_denied"
    DATA_CLASS_DENIED = "data_class_denied"
    POLICY_DENIED = "policy_denied"
    PROVIDER_ERROR = "provider_error"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    BUDGET_EXCEEDED = "budget_exceeded"
    INVALID_REQUEST = "invalid_request"


@dataclass(frozen=True, slots=True)
class ModelDefinition:
    """Immutable, allowlisted metadata for a production model deployment."""

    name: str
    version: str
    provider: str
    capabilities: frozenset[ModelCapability] = field(default_factory=frozenset)
    allowed_data_classes: frozenset[DataClass] = field(
        default_factory=lambda: frozenset(DataClass)
    )
    context_window: int = 0
    max_output_tokens: int = 0
    enabled: bool = True

    def __post_init__(self) -> None:
        for value, label in (
            (self.name, "model name"),
            (self.version, "model version"),
            (self.provider, "provider"),
        ):
            if not value.strip():
                raise ValueError(f"{label} is required")
        if self.context_window < 0 or self.max_output_tokens < 0:
            raise ValueError("model limits cannot be negative")


@dataclass(frozen=True, slots=True)
class ModelMessage:
    role: str
    content: str

    def __post_init__(self) -> None:
        if self.role not in {"system", "user", "assistant", "tool"}:
            raise ValueError("unsupported message role")


@dataclass(frozen=True, slots=True)
class ModelRequest:
    context: RequestContext
    model: str | None
    messages: Sequence[ModelMessage]
    required_capabilities: frozenset[ModelCapability] = field(default_factory=frozenset)
    data_class: DataClass = DataClass.INTERNAL
    max_output_tokens: int = 1024
    temperature: float = 0.0
    request_id: str = ""

    def __post_init__(self) -> None:
        if not self.messages:
            raise ValueError("at least one message is required")
        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0 and 2")
        if not self.request_id.strip():
            raise ValueError("request_id is required")


@dataclass(frozen=True, slots=True)
class ModelResponse:
    success: bool
    output: str | None = None
    model: str | None = None
    provider: str | None = None
    usage: Mapping[str, int] = field(default_factory=dict)
    error_code: ModelErrorCode | None = None
    retryable: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.success and self.error_code is not None:
            raise ValueError("successful response cannot contain an error code")
        if not self.success and self.error_code is None:
            raise ValueError("failed response requires an error code")


class ModelProvider(Protocol):
    """Provider adapter; SDKs and network clients remain outside the kernel."""

    def generate(self, definition: ModelDefinition, request: ModelRequest) -> ModelResponse: ...


class ModelPolicy(Protocol):
    """Optional policy hook evaluated before a provider is invoked."""

    def allow(self, context: RequestContext, definition: ModelDefinition, request: ModelRequest) -> bool: ...
