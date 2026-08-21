"""MCP-facing compatibility contracts and enterprise interoperability exports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .interoperability import (
    MCPAuthorizationContext,
    MCPProtocolVersion,
    MCPRequest,
    MCPRequestValidator,
    MCPToolAnnotations,
    MCPToolCatalog,
    MCPToolCatalogEntry,
)


@dataclass(frozen=True, slots=True)
class MCPToolDefinition:
    name: str
    version: str
    input_schema: Mapping[str, object]
    output_schema: Mapping[str, object] | None = None
    annotations: MCPToolAnnotations = MCPToolAnnotations()
    required_scopes: frozenset[str] = frozenset()
    risk_level: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.version.strip():
            raise ValueError("MCP tool name and version are required")
        if not 0 <= self.risk_level <= 5:
            raise ValueError("risk_level must be between 0 and 5")


@dataclass(frozen=True, slots=True)
class MCPToolCall:
    tool: MCPToolDefinition
    arguments: Mapping[str, object]
    request_id: str
    authorization_reference: str
    tenant_id: str = ""
    protocol_version: MCPProtocolVersion = MCPProtocolVersion.V2026_07_28

    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.authorization_reference.strip():
            raise ValueError("request_id and authorization_reference are required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")


__all__ = [
    "MCPAuthorizationContext", "MCPProtocolVersion", "MCPRequest", "MCPRequestValidator",
    "MCPToolAnnotations", "MCPToolCall", "MCPToolCatalog", "MCPToolCatalogEntry", "MCPToolDefinition",
]
