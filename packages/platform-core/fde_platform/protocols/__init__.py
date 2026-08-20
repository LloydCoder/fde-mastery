"""Interoperability protocol boundaries; security remains platform-owned."""

from .a2a import AgentMessage, A2AEnvelope
from .mcp import MCPToolCall, MCPToolDefinition

__all__ = ["AgentMessage", "A2AEnvelope", "MCPToolCall", "MCPToolDefinition"]
