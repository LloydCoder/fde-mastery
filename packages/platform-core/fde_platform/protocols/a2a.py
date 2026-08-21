"""A2A compatibility contracts and enterprise interoperability exports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .interoperability import (
    A2AAgentRegistry,
    A2ARequest,
    A2ATaskBridge,
    A2ATaskRef,
    A2ATaskState,
    AgentCard,
    AgentInterface,
    AgentSkill,
    SecurityScheme,
    authorize_a2a,
    validate_agent_card_endpoint,
)


@dataclass(frozen=True, slots=True)
class AgentMessage:
    message_id: str
    sender_agent: str
    recipient_agent: str
    capability: str
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        for value in (self.message_id, self.sender_agent, self.recipient_agent, self.capability):
            if not value.strip():
                raise ValueError("A2A message identifiers are required")


@dataclass(frozen=True, slots=True)
class A2AEnvelope:
    message: AgentMessage
    tenant_id: str
    authorization_reference: str
    ttl_seconds: int = 60

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.authorization_reference.strip():
            raise ValueError("tenant_id and authorization_reference are required")
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")


__all__ = [
    "A2AAgentRegistry", "A2AEnvelope", "A2ARequest", "A2ATaskBridge", "A2ATaskRef", "A2ATaskState",
    "AgentCard", "AgentInterface", "AgentMessage", "AgentSkill", "SecurityScheme", "authorize_a2a",
    "validate_agent_card_endpoint",
]
