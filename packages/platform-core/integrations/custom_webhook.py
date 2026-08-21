"""Secure generic webhook integration.

This adapter is deliberately fail-closed: production endpoints must be HTTPS and explicitly
allowlisted. Authentication material is supplied by a managed secrets provider, never stored
in the integration object or repository.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

import requests

from .http import OutboundHTTPClient, OutboundURLPolicy


class CustomWebhook:
    """POST JSON to an explicitly allowlisted downstream webhook."""

    def __init__(self, endpoint_url: str | None = None, headers: Mapping[str, str] | None = None):
        self.endpoint_url = endpoint_url or os.environ.get("CUSTOM_WEBHOOK_URL", "")
        configured = os.environ.get("CUSTOM_WEBHOOK_ALLOWED_HOSTS", "")
        allowed_hosts = frozenset(host.strip().lower() for host in configured.split(",") if host.strip())
        if self.endpoint_url and not allowed_hosts:
            raise RuntimeError("CUSTOM_WEBHOOK_ALLOWED_HOSTS must explicitly allow the webhook host")
        self._client = OutboundHTTPClient(OutboundURLPolicy(allowed_hosts), requests)
        self.headers = {"Content-Type": "application/json", **dict(headers or {})}

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.endpoint_url:
            raise RuntimeError("custom webhook endpoint is not configured")
        response = self._client.request("POST", self.endpoint_url, json=payload, headers=self.headers, timeout=10)
        return {"status": "sent", "code": response.status_code, "response": response.text[:200]}

    def send_triage_result(self, client_id: str, domain: str, result: dict[str, Any]) -> dict[str, Any]:
        from datetime import datetime, timezone

        return self.send({
            "event": "triage_complete",
            "client_id": client_id,
            "domain": domain,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": result,
        })
