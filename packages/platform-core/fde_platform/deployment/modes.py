"""Explicit shared, isolated and dedicated deployment profiles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeploymentMode(str, Enum):
    SHARED = "shared"
    ISOLATED = "isolated"
    DEDICATED = "dedicated"


@dataclass(frozen=True, slots=True)
class DeploymentProfile:
    mode: DeploymentMode
    region: str
    dedicated_database: bool
    dedicated_keys: bool
    dedicated_network: bool

    @classmethod
    def for_mode(cls, mode: DeploymentMode, region: str) -> "DeploymentProfile":
        if not region.strip():
            raise ValueError("region is required")
        if mode is DeploymentMode.SHARED:
            return cls(mode, region, False, False, False)
        if mode is DeploymentMode.ISOLATED:
            return cls(mode, region, True, True, True)
        return cls(mode, region, True, True, True)
