"""Bridge integrations into the existing Tool Gateway without creating a second executor."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from fde_platform.tools import InMemoryToolGateway
from fde_platform.tools.models import ToolCapability, ToolDefinition

from .plane import IntegrationBinding


def register_integration_action(
    gateway: InMemoryToolGateway,
    *,
    binding: IntegrationBinding,
    action: str,
    handler: Callable[[dict[str, Any]], Any],
    capabilities: frozenset[ToolCapability] = frozenset({ToolCapability.EXTERNAL_NETWORK}),
    requires_approval: bool = True,
) -> str:
    """Register a tenant integration action as an ordinary gateway tool.

    The integration plane owns configuration/credentials; the existing Tool Gateway owns
    authorization, capability checks, approval and idempotency.
    """
    if not action.strip():
        raise ValueError("action is required")
    name = f"integration:{binding.definition.provider}:{binding.integration_id}:{action}"
    gateway.register(
        ToolDefinition(
            name=name,
            version=binding.definition.version,
            description=f"{binding.definition.provider} integration action: {action}",
            capabilities=capabilities,
            input_schema={"type": "object"},
            requires_approval=requires_approval,
        ),
        handler,
    )
    return name
