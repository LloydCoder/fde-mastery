"""Stable HTTP API contracts.

ProblemDetails follows RFC 9457 semantics. IdempotencyKey validation follows the
current IETF HTTPAPI draft without treating the draft as a finalized standard.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Generic, TypeVar
from uuid import UUID


T = TypeVar("T")
_IDEMPOTENCY_PATTERN = re.compile(r"^[\x21-\x7E]{1,255}$")


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    value: str

    def __post_init__(self) -> None:
        if not _IDEMPOTENCY_PATTERN.fullmatch(self.value):
            raise ValueError("Idempotency-Key must contain 1-255 visible ASCII characters")


@dataclass(frozen=True, slots=True)
class RequestMetadata:
    request_id: str
    idempotency_key: IdempotencyKey | None = None

    def __post_init__(self) -> None:
        try:
            UUID(self.request_id)
        except (ValueError, AttributeError) as exc:
            raise ValueError("request_id must be a UUID") from exc


@dataclass(frozen=True, slots=True)
class ProblemDetails:
    type: str = "about:blank"
    title: str = "Request failed"
    status: int = 500
    detail: str | None = None
    instance: str | None = None
    code: str | None = None
    request_id: str | None = None
    retryable: bool = False

    def __post_init__(self) -> None:
        if not self.type.strip() or not self.title.strip():
            raise ValueError("problem type and title are required")
        if self.status < 400 or self.status > 599:
            raise ValueError("problem status must be an HTTP error status")


@dataclass(frozen=True, slots=True)
class Page(Generic[T]):
    items: tuple[T, ...]
    limit: int
    next_cursor: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 100:
            raise ValueError("limit must be between 1 and 100")
