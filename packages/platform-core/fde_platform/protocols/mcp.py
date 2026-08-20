"""Minimal MCP-facing contracts with explicit platform authorization boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class MCPToolDefinition:
    name: str
    version: str
    input_schema: Mapping[str, object]
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

    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.authorization_reference.strip():
            raise ValueError("request_id and authorization_reference are required")
