"""Tenant-scoped tool catalog and fail-closed execution gateway."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .policy import requires_human_approval


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    handler: Callable[[dict[str, Any]], Any]
    mutating: bool = False


class ToolCatalog:
    """Explicitly registered tools; unknown tools cannot be executed."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if not definition.name or definition.name.strip() != definition.name:
            raise ValueError("tool name must be non-empty and canonical")
        if definition.name in self._tools:
            raise ValueError(f"tool already registered: {definition.name}")
        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"tool is not registered: {name}") from exc


class ToolExecutionDenied(PermissionError):
    """Raised when a tool is outside the agent's declared execution policy."""


class CustomAgentToolGateway:
    """Enforce tenant tool allowlists and human approval before tool execution."""

    def __init__(self, catalog: ToolCatalog) -> None:
        self._catalog = catalog

    def execute(
        self,
        *,
        tenant_id: str,
        allowed_tools: tuple[str, ...],
        tool_name: str,
        payload: dict[str, Any],
        approved_actions: frozenset[str] = frozenset(),
    ) -> Any:
        if not tenant_id:
            raise ToolExecutionDenied("tenant identity is required")
        if tool_name not in allowed_tools:
            raise ToolExecutionDenied("tool is not in the agent allowlist")
        definition = self._catalog.get(tool_name)
        if definition.mutating or requires_human_approval(tool_name):
            if tool_name not in approved_actions:
                raise ToolExecutionDenied("human approval is required before this action")
        if not isinstance(payload, dict):
            raise TypeError("tool payload must be a dictionary")
        return definition.handler(payload)
