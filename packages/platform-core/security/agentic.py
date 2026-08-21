"""Runtime security controls for autonomous and tool-using agents.

These controls are defense-in-depth. They never replace the platform PDP, identity boundary,
Tool Gateway or human-approval system; they make unsafe agent decisions fail closed before they
reach those side-effect boundaries.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrustLevel(str, Enum):
    UNTRUSTED = "untrusted"
    EXTERNAL = "external"
    USER = "user"
    VERIFIED = "verified"


@dataclass(frozen=True, slots=True)
class AgentSecurityContext:
    tenant_id: str
    agent_id: str
    request_id: str
    trust: TrustLevel
    confidence: float
    autonomy_budget: int
    allowed_capabilities: frozenset[str] = field(default_factory=frozenset)
    approval_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.agent_id.strip() or not self.request_id.strip():
            raise ValueError("tenant, agent and request identity are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.autonomy_budget < 0:
            raise ValueError("autonomy_budget cannot be negative")


@dataclass(frozen=True, slots=True)
class AgentAction:
    tool_name: str
    tenant_id: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    risk: RiskTier = RiskTier.LOW
    irreversible: bool = False
    external_side_effect: bool = False


@dataclass(frozen=True, slots=True)
class SecurityDecision:
    allowed: bool
    reason: str
    requires_human_approval: bool = False


class AgentActionSecurityGate:
    """Fail-closed pre-action gate for autonomous agent decisions."""

    _CONFIDENCE_MINIMUM = {
        RiskTier.LOW: 0.0,
        RiskTier.MEDIUM: 0.70,
        RiskTier.HIGH: 0.90,
        RiskTier.CRITICAL: 0.99,
    }

    def evaluate(self, context: AgentSecurityContext, action: AgentAction) -> SecurityDecision:
        if action.tenant_id != context.tenant_id:
            return SecurityDecision(False, "tenant_context_mismatch")
        if not action.capabilities.issubset(context.allowed_capabilities):
            return SecurityDecision(False, "capability_not_granted")
        if context.autonomy_budget <= 0 and (action.external_side_effect or action.irreversible):
            return SecurityDecision(False, "autonomy_budget_exhausted")
        if context.confidence < self._CONFIDENCE_MINIMUM[action.risk]:
            return SecurityDecision(False, "confidence_below_risk_threshold")
        high_impact = action.risk in {RiskTier.HIGH, RiskTier.CRITICAL} or action.irreversible
        if high_impact and not context.approval_reference:
            return SecurityDecision(False, "human_approval_required", True)
        if action.irreversible and context.trust in {TrustLevel.UNTRUSTED, TrustLevel.EXTERNAL}:
            return SecurityDecision(False, "untrusted_context_cannot_perform_irreversible_action")
        return SecurityDecision(True, "agent_action_allowed")


_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all|any|previous|prior)\s+instructions", re.I),
    re.compile(r"(reveal|print|dump|show)\s+(the\s+)?(system|developer)\s+prompt", re.I),
    re.compile(r"bypass\s+(security|policy|approval|authorization)", re.I),
    re.compile(r"disable\s+(audit|logging|security|policy)", re.I),
    re.compile(r"act\s+as\s+(root|administrator|system)", re.I),
    re.compile(r"send\s+(all|the)\s+(secrets|credentials|tokens)", re.I),
)


@dataclass(frozen=True, slots=True)
class ThreatIndicator:
    category: str
    evidence: str
    severity: RiskTier


def scan_untrusted_text(text: str) -> tuple[ThreatIndicator, ...]:
    """Cheap deterministic screening; a positive result is a signal, never an authorization decision."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    indicators: list[ThreatIndicator] = []
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            indicators.append(ThreatIndicator("prompt_injection", match.group(0)[:120], RiskTier.HIGH))
    return tuple(indicators)


_SECRET_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
)


def redact_sensitive_output(text: str) -> tuple[str, tuple[str, ...]]:
    """Redact high-confidence credential patterns before output leaves a trust boundary."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    redacted = text
    categories: list[str] = []
    for category, pattern in _SECRET_PATTERNS:
        if pattern.search(redacted):
            categories.append(category)
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted, tuple(categories)


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    record_id: str
    tenant_id: str
    source: str
    trust: TrustLevel
    content: str
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.record_id.strip() or not self.tenant_id.strip() or not self.source.strip():
            raise ValueError("memory record identity and source are required")
        if self.trust is TrustLevel.UNTRUSTED and not self.provenance:
            raise ValueError("untrusted memory requires provenance")


def filter_memory(records: Iterable[MemoryRecord], *, tenant_id: str, minimum_trust: TrustLevel = TrustLevel.USER) -> tuple[MemoryRecord, ...]:
    order = {
        TrustLevel.UNTRUSTED: 0,
        TrustLevel.EXTERNAL: 1,
        TrustLevel.USER: 2,
        TrustLevel.VERIFIED: 3,
    }
    threshold = order[minimum_trust]
    return tuple(record for record in records if record.tenant_id == tenant_id and order[record.trust] >= threshold)
