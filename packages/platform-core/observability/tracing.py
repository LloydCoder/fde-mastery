"""Opt-in OpenTelemetry tracing with safe no-op behavior."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
except ImportError:  # optional dependency
    trace = None  # type: ignore[assignment]


def configure_tracing() -> bool:
    if trace is None or os.getenv("OTEL_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        return False
    service_name = os.getenv("OTEL_SERVICE_NAME", "fde-mastery-platform")
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    if endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    return True


@contextmanager
def span(name: str, **attributes: str) -> Iterator[object]:
    if trace is None:
        yield None
        return
    tracer = trace.get_tracer("fde-mastery-platform")
    with tracer.start_as_current_span(name) as current:
        for key, value in attributes.items():
            current.set_attribute(key, value)
        yield current
