"""Small, dependency-free Python client for the versioned FDE Mastery API."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Mapping
from typing import Any


class ApiError(RuntimeError):
    """Structured HTTP API failure."""

    def __init__(self, status: int, body: Any, request_id: str | None = None) -> None:
        self.status = status
        self.body = body
        self.request_id = request_id
        super().__init__(f"FDE Mastery API request failed with HTTP {status}")


class FDEMasteryClient:
    def __init__(self, base_url: str, *, api_key: str | None = None, bearer_token: str | None = None, timeout: float = 10.0, max_retries: int = 2) -> None:
        normalized = base_url.rstrip("/")
        if not normalized.startswith("https://") and not normalized.startswith("http://localhost") and not normalized.startswith("http://127.0.0.1"):
            raise ValueError("base_url must use HTTPS outside localhost")
        if timeout <= 0 or timeout > 120:
            raise ValueError("timeout must be between 0 and 120 seconds")
        if max_retries < 0 or max_retries > 5:
            raise ValueError("max_retries must be between 0 and 5")
        if api_key and bearer_token:
            raise ValueError("provide either api_key or bearer_token, not both")
        self.base_url = normalized
        self.api_key = api_key
        self.bearer_token = bearer_token
        self.timeout = timeout
        self.max_retries = max_retries

    def _request(self, method: str, path: str, *, payload: Mapping[str, Any] | None = None, idempotency_key: str | None = None) -> Any:
        if not path.startswith("/"):
            raise ValueError("path must begin with /")
        if method in {"POST", "PATCH"} and not idempotency_key and method != "GET":
            raise ValueError("mutating requests require an idempotency_key")
        request_id = str(uuid.uuid4())
        headers = {"Accept": "application/json", "User-Agent": "fde-mastery-python/1.20", "X-Request-ID": request_id}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        body = json.dumps(payload, separators=(",", ":")).encode() if payload is not None else None
        request = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
        attempts = 0
        while True:
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8")
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8", errors="replace")
                try:
                    parsed: Any = json.loads(raw) if raw else None
                except json.JSONDecodeError:
                    parsed = {"detail": "invalid JSON error response"}
                if exc.code not in {429, 502, 503, 504} or attempts >= self.max_retries:
                    raise ApiError(exc.code, parsed, exc.headers.get("X-Request-ID")) from exc
                if method in {"POST", "PATCH"} and not idempotency_key:
                    raise ApiError(exc.code, parsed, exc.headers.get("X-Request-ID")) from exc
                retry_after = exc.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else min(2**attempts, 8)
                time.sleep(delay)
                attempts += 1
            except urllib.error.URLError as exc:
                if attempts >= self.max_retries or method in {"POST", "PATCH"} and not idempotency_key:
                    raise RuntimeError("FDE Mastery API transport failure") from exc
                time.sleep(min(2**attempts, 8))
                attempts += 1

    def health(self) -> Any:
        return self._request("GET", "/v1/health")

    def capabilities(self) -> Any:
        return self._request("GET", "/v1/capabilities")

    def triage(self, client_id: str, domain: str, payload: Mapping[str, Any], *, idempotency_key: str) -> Any:
        if not client_id or not domain:
            raise ValueError("client_id and domain are required")
        return self._request("POST", f"/v1/triage/{client_id}/{domain}", payload=payload, idempotency_key=idempotency_key)
