"""Metrics contracts with explicit cardinality and value validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol


@dataclass(frozen=True)
class MetricPoint:
    """A single metric sample with bounded labels."""

    name: str
    value: float
    attributes: Mapping[str, str] = field(default_factory=dict)
    unit: str | None = None

    def __post_init__(self) -> None:
        if not self.name or len(self.name) > 128:
            raise ValueError("metric name must contain 1-128 characters")
        if len(self.attributes) > 20:
            raise ValueError("metric attribute cardinality is too large")
        if any(len(key) > 64 or len(value) > 128 for key, value in self.attributes.items()):
            raise ValueError("metric attributes exceed bounded dimensions")


class MetricsSink(Protocol):
    """Port implemented by an OpenTelemetry metrics adapter."""

    def record(self, point: MetricPoint) -> None: ...
