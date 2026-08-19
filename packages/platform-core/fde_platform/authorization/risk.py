"""Risk classification for authorization decisions.

Risk is an input to policy, never a reason to bypass authorization. The model is
small and deterministic so it can later be backed by a centralized policy
service without changing callers.
"""
from __future__ import annotations

from enum import IntEnum


class RiskTier(IntEnum):
    LOW = 10
    MEDIUM = 20
    HIGH = 30
    CRITICAL = 40

    @classmethod
    def from_name(cls, value: str) -> "RiskTier":
        try:
            return cls[value.strip().upper()]
        except (KeyError, AttributeError) as exc:
            raise ValueError(f"unknown risk tier: {value!r}") from exc

    @property
    def requires_human_approval(self) -> bool:
        return self >= RiskTier.HIGH
