"""Generic custom webhook integration for arbitrary downstream systems."""

import json
import os
from typing import Any, Dict, Optional


class CustomWebhook:
    """Sends POST requests to custom webhook endpoints."""

    def __init__(self, endpoint_url: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        self.endpoint_url = endpoint_url or os.environ.get("CUSTOM_WEBHOOK_URL", "")
        self.headers = headers or {"Content-Type": "application/json"}

    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send payload to configured webhook endpoint."""
        if self.endpoint_url:
            try:
                import requests
                resp = requests.post(self.endpoint_url, json=payload, headers=self.headers, timeout=10)
                return {"status": "sent", "code": resp.status_code, "response": resp.text[:200]}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        print(f"[WEBHOOK MOCK] Endpoint: {self.endpoint_url or 'NOT_CONFIGURED'}")
        print(f"[WEBHOOK MOCK] Payload: {json.dumps(payload, indent=2)}")
        return {"status": "mock_sent"}

    def send_triage_result(self, client_id: str, domain: str, result: Dict[str, Any]) -> Dict[str, Any]:
        return self.send({
            "event": "triage_complete",
            "client_id": client_id,
            "domain": domain,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "result": result,
        })
