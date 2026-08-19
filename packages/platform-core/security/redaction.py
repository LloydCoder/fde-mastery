"""Deterministic redaction for logs, audit metadata and model outputs."""
from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEYS = frozenset({"password", "token", "secret", "api_key", "authorization", "ssn", "credit_card", "iban", "access_token"})
_PATTERNS = (
    re.compile(r"\b(?:sk|pk)-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\b\d{13,19}\b"),
)


def redact_text(value: str) -> str:
    result = value
    for pattern in _PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): "[REDACTED]" if str(k).lower() in SENSITIVE_KEYS else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, tuple):
        return tuple(redact(v) for v in value)
    if isinstance(value, str):
        return redact_text(value)
    return value
