"""FastAPI instrumentation for request, router and dependency telemetry."""

from __future__ import annotations

import os


def instrument_app(app) -> bool:
    """Install OpenTelemetry FastAPI instrumentation when explicitly enabled."""
    if os.getenv("OTEL_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        return False
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError as exc:
        raise RuntimeError("Install opentelemetry-instrumentation-fastapi to enable API tracing") from exc
    FastAPIInstrumentor.instrument_app(app, excluded_urls=os.getenv("OTEL_EXCLUDED_URLS", "health").strip())
    return True
