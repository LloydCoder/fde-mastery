"""Compatibility export for legacy Month 1-6 adapter imports.

New code should import from ``shared_orchestrator.domain_agent``.
"""

from shared_orchestrator.domain_agent import DomainAgent, DomainAgentResult

__all__ = ["DomainAgent", "DomainAgentResult"]
