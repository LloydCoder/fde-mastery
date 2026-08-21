"""Provider-neutral, provenance-bound knowledge and memory contracts.

The module provides the trust and isolation boundary for durable context. It does
not implement embeddings, vector databases, ranking models or an LLM. Retrieval
is treated as untrusted data and never as an authorization source.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping


_MAX_CONTENT = 1_000_000
_MAX_TAGS = 32
_MAX_METADATA = 32
_MAX_KEY = 64
_MAX_VALUE = 256
_MAX_SOURCE = 128


class MemoryTrust(str, Enum):
    UNTRUSTED = "untrusted"
    EXTERNAL = "external"
    USER = "user"
    VERIFIED = "verified"


_TRUST_ORDER = {
    MemoryTrust.UNTRUSTED: 0,
    MemoryTrust.EXTERNAL: 1,
    MemoryTrust.USER: 2,
    MemoryTrust.VERIFIED: 3,
}


_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all|any|previous|prior)\s+instructions", re.I),
    re.compile(r"(reveal|print|dump|show)\s+(the\s+)?(system|developer)\s+prompt", re.I),
    re.compile(r"bypass\s+(security|policy|approval|authorization)", re.I),
    re.compile(r"disable\s+(audit|logging|security|policy)", re.I),
)


def _id(value: str, name: str, limit: int = _MAX_VALUE) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError(f"{name} is required and must be bounded")
    return value.strip()


def _metadata(values: Mapping[str, str]) -> dict[str, str]:
    if len(values) > _MAX_METADATA:
        raise ValueError("metadata exceeds maximum cardinality")
    result: dict[str, str] = {}
    for key, value in values.items():
        result[_id(key, "metadata key", _MAX_KEY)] = _id(value, "metadata value", _MAX_VALUE)
    return result


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def content_digest(content: str) -> str:
    if not isinstance(content, str):
        raise TypeError("content must be a string")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _injection_signal(content: str) -> bool:
    return any(pattern.search(content) for pattern in _INJECTION_PATTERNS)


@dataclass(frozen=True, slots=True)
class KnowledgeRecord:
    record_id: str
    tenant_id: str
    scope_id: str
    source: str
    trust: MemoryTrust
    content: str
    created_at: datetime
    expires_at: datetime | None = None
    version: int = 1
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
    digest: str = ""
    poisoned: bool = False

    def __post_init__(self) -> None:
        _id(self.record_id, "record_id")
        _id(self.tenant_id, "tenant_id")
        _id(self.scope_id, "scope_id")
        _id(self.source, "source", _MAX_SOURCE)
        if not isinstance(self.content, str) or not self.content or len(self.content) > _MAX_CONTENT:
            raise ValueError("content is required and must be bounded")
        _aware(self.created_at, "created_at")
        if self.expires_at is not None:
            _aware(self.expires_at, "expires_at")
            if self.expires_at <= self.created_at:
                raise ValueError("expires_at must be after created_at")
        if self.version < 1:
            raise ValueError("version must be positive")
        if len(self.tags) > _MAX_TAGS:
            raise ValueError("tags exceed maximum cardinality")
        for tag in self.tags:
            _id(tag, "tag", 64)
        object.__setattr__(self, "metadata", _metadata(self.metadata))
        calculated = content_digest(self.content)
        if self.digest and self.digest != calculated:
            raise ValueError("content digest mismatch")
        object.__setattr__(self, "digest", calculated)
        if self.poisoned or _injection_signal(self.content):
            object.__setattr__(self, "poisoned", True)

    def is_live_at(self, when: datetime) -> bool:
        _aware(when, "when")
        return self.created_at <= when and (self.expires_at is None or when < self.expires_at)


@dataclass(frozen=True, slots=True)
class RetrievalPolicy:
    minimum_trust: MemoryTrust = MemoryTrust.USER
    allow_external: bool = False
    allow_poisoned: bool = False
    require_live: bool = True


@dataclass(frozen=True, slots=True)
class RetrievalDecision:
    allowed: bool
    reason: str
    record: KnowledgeRecord | None = None


class KnowledgeStore:
    """Reference store; production persistence/indexing remains behind existing storage ports."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], KnowledgeRecord] = {}

    def put(self, record: KnowledgeRecord) -> None:
        key = (record.tenant_id, record.record_id)
        current = self._records.get(key)
        if current is not None and record.version <= current.version:
            raise ValueError("record version must increase")
        self._records[key] = record

    def get(self, tenant_id: str, record_id: str) -> KnowledgeRecord | None:
        return self._records.get((tenant_id, record_id))

    def retrieve(
        self,
        tenant_id: str,
        scope_id: str,
        record_id: str,
        *,
        policy: RetrievalPolicy = RetrievalPolicy(),
        now: datetime | None = None,
    ) -> RetrievalDecision:
        record = self.get(tenant_id, record_id)
        if record is None:
            return RetrievalDecision(False, "record_not_found")
        if record.scope_id != scope_id:
            return RetrievalDecision(False, "scope_mismatch")
        if _TRUST_ORDER[record.trust] < _TRUST_ORDER[policy.minimum_trust]:
            return RetrievalDecision(False, "trust_below_policy")
        if record.trust is MemoryTrust.EXTERNAL and not policy.allow_external:
            return RetrievalDecision(False, "external_memory_blocked")
        if record.poisoned and not policy.allow_poisoned:
            return RetrievalDecision(False, "poisoned_memory_blocked")
        if policy.require_live:
            when = now or datetime.now(timezone.utc)
            if not record.is_live_at(when):
                return RetrievalDecision(False, "record_expired")
        return RetrievalDecision(True, "record_retrievable", record)
