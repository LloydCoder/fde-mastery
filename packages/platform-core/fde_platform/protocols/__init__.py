"""Interoperability protocol boundaries; security remains platform-owned."""

from .a2a import (
    A2AAgentRegistry, A2AEnvelope, A2ARequest, A2ATaskBridge, A2ATaskRef, A2ATaskState,
    AgentMessage, AgentCard, AgentInterface, AgentSkill, SecurityScheme, authorize_a2a,
    validate_agent_card_endpoint,
)
from .mcp import (
    MCPAuthorizationContext, MCPProtocolVersion, MCPRequest, MCPRequestValidator, MCPToolAnnotations,
    MCPToolCall, MCPToolCatalog, MCPToolCatalogEntry, MCPToolDefinition,
)

__all__ = [
    "A2AAgentRegistry", "A2AEnvelope", "A2ARequest", "A2ATaskBridge", "A2ATaskRef", "A2ATaskState",
    "AgentCard", "AgentInterface", "AgentMessage", "AgentSkill", "SecurityScheme", "authorize_a2a",
    "MCPAuthorizationContext", "MCPProtocolVersion", "MCPRequest", "MCPRequestValidator",
    "MCPToolAnnotations", "MCPToolCall", "MCPToolCatalog", "MCPToolCatalogEntry", "MCPToolDefinition",
    "validate_agent_card_endpoint",
]
