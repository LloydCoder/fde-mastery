"""Structured, privacy-aware telemetry contracts for platform operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Protocol


@dataclass(frozen=True)
class Observation:
    """A low-cardinality observation safe to export to a telemetry backend."""

    name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: Mapping[str, str | int | float | bool] = field(default_factory=dict)
    duration_ms: float | None = None
    status: str = "ok"

    def __post_init__(self) -> None:
        if not self.name or len(self.name) > 128:
            raise ValueError("observation name must contain 1-128 characters")
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")


class TelemetrySink(Protocol):
    """Port implemented by an OpenTelemetry or other telemetry adapter."""

    def record(self, observation: Observation) -> None: ...
