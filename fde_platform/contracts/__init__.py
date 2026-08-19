"""Stable contracts shared across the FDE platform."""

from .agent import AgentRequest, AgentResult
from .domain import DomainDescriptor
from .execution import ExecutionContext

__all__ = [
    "AgentRequest",
    "AgentResult",
    "DomainDescriptor",
    "ExecutionContext",
]
