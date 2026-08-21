"""Tinlance gateway integration contract.

Keeps the external gateway/mastery HTTP contract explicit and testable.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


VALID_DOMAINS = (
    "cybersecurity",
    "finance",
    "healthtech",
    "logistics",
    "legal",
    "revops",
    "procurement",
    "custom",
)


class TinlanceAgentRequest(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any]


class TinlanceAgentResponse(BaseModel):
    """Loose response envelope because domain agents return domain-specific data."""

    model_config = {"extra": "allow"}
