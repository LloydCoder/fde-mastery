"""Agent execution port."""

from typing import Protocol

from fde_platform.contracts.agent import AgentRequest, AgentResult


class AgentPort(Protocol):
    """Application-facing capability implemented by concrete agent runtimes."""

    def execute(self, request: AgentRequest) -> AgentResult:
        """Execute an agent request and return a normalized result."""
