"""Optional OpenTelemetry tracing with safe no-op behavior."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from opentelemetry import trace


def configure_tracing() -> None:
    """Configure SDK/exporter only when explicitly enabled."""
    if os.getenv("FDE_OTEL_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        return
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "fde-mastery-platform")})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)


@contextmanager
def span(name: str, **attributes: str) -> Iterator[object]:
    tracer = trace.get_tracer("fde-mastery-platform")
    with tracer.start_as_current_span(name) as current:
        for key, value in attributes.items():
            current.set_attribute(key, value)
        yield current
