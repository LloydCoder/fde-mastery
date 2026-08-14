"""Small in-process metrics collector with Prometheus text output."""

from __future__ import annotations

from collections import Counter
from threading import Lock


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests = Counter()
        self._latency_ms = 0.0
        self._errors = Counter()

    def observe_request(self, method: str, path: str, status: int, duration_ms: float) -> None:
        with self._lock:
            self._requests[(method, path, status)] += 1
            self._latency_ms += duration_ms
            if status >= 500:
                self._errors[(method, path)] += 1

    def prometheus(self) -> str:
        with self._lock:
            lines = [
                "# HELP fde_http_requests_total HTTP requests handled.",
                "# TYPE fde_http_requests_total counter",
            ]
            for (method, path, status), value in sorted(self._requests.items()):
                lines.append(
                    f'fde_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {value}'
                )
            lines.extend([
                "# HELP fde_http_request_duration_ms_total Sum of request durations in milliseconds.",
                "# TYPE fde_http_request_duration_ms_total counter",
                f"fde_http_request_duration_ms_total {self._latency_ms:.3f}",
            ])
            return "\n".join(lines) + "\n"


metrics = Metrics()
