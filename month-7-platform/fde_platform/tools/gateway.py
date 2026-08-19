"""Fail-closed tool gateway with capability and idempotency enforcement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..identity import RequestContext
from .models import ToolCall, ToolCapability, ToolDefinition, ToolResult


class ToolGateway(ABC):
    """Port through which agents may invoke registered tools."""

    @abstractmethod
    def register(self, definition: ToolDefinition, handler: Callable[[dict[str, Any]], Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def invoke(self, context: RequestContext, call: ToolCall) -> ToolResult:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class _RegisteredTool:
    definition: ToolDefinition
    handler: Callable[[dict[str, Any]], Any]


class InMemoryToolGateway(ToolGateway):
    """Deterministic reference gateway; production adapters can implement the same port."""

    def __init__(self) -> None:
        self._tools: dict[str, _RegisteredTool] = {}
        self._results: dict[tuple[str, str], ToolResult] = {}

    def register(self, definition: ToolDefinition, handler: Callable[[dict[str, Any]], Any]) -> None:
        if definition.name in self._tools:
            raise ValueError(f"tool already registered: {definition.name}")
        self._tools[definition.name] = _RegisteredTool(definition, handler)

    def invoke(self, context: RequestContext, call: ToolCall) -> ToolResult:
        registered = self._tools.get(call.tool_name)
        if registered is None:
            return ToolResult(False, error_code="tool_not_found")
        if call.request_id != context.request_id:
            return ToolResult(False, error_code="request_context_mismatch")
        if not call.capabilities.issubset(registered.definition.capabilities):
            return ToolResult(False, error_code="capability_denied")
        if registered.definition.requires_approval:
            return ToolResult(False, error_code="approval_required")
        key = (call.tool_name, call.idempotency_key)
        if key in self._results:
            return self._results[key]
        try:
            result = registered.handler(dict(call.arguments))
        except Exception:
            result = ToolResult(False, error_code="tool_execution_failed", retryable=True)
        if not isinstance(result, ToolResult):
            result = ToolResult(True, output=result)
        self._results[key] = result
        return result
