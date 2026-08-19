"""Canonical tenant and environment identifiers.

These primitives are intentionally framework-neutral. They provide the invariant
that every tenant-scoped operation carries an explicit, validated tenant and
execution environment. They do not perform authorization themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import NewType

TenantId = NewType("TenantId", str)

_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{2,62}$")


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass(frozen=True, slots=True)
class TenantRef:
    tenant_id: TenantId
    environment: Environment

    def __post_init__(self) -> None:
        value = str(self.tenant_id).strip()
        if not _ID_RE.fullmatch(value):
            raise ValueError("tenant_id must be 3-63 chars, lowercase, and start with a letter")
        object.__setattr__(self, "tenant_id", TenantId(value))

    @property
    def key(self) -> str:
        return f"{self.tenant_id}:{self.environment.value}"
