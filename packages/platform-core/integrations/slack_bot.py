"""Slack bot integration for alerting analysts and sales teams."""

import json
import os
from typing import Any, Dict, Optional


class SlackBot:
    """Posts alerts to Slack channels for triage and escalation events."""

    def __init__(self, webhook_url: Optional[str] = None, channel: str = "#fde-alerts"):
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL", "")
        self.channel = channel

    def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a formatted Slack message."""
        color_map = {"info": "#36a64f", "warning": "#ff9900", "critical": "#ff0000"}
        field_values: list[dict[str, Any]] = [
            {"title": k, "value": str(v), "short": True}
            for k, v in (fields or {}).items()
        ]
        payload: dict[str, Any] = {
            "channel": self.channel,
            "username": "FDE-Mastery-Bot",
            "icon_emoji": ":robot_face:",
            "attachments": [{
                "color": color_map.get(severity, "#36a64f"),
                "title": title,
                "text": message,
                "fields": field_values,
                "footer": "FDE Mastery Platform",
                "ts": int(__import__("time").time()),
            }],
        }

        if self.webhook_url:
            try:
                import requests
                resp = requests.post(self.webhook_url, json=payload, timeout=5)
                return {"status": "sent", "code": resp.status_code}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        print(f"[SLACK MOCK] Channel: {self.channel}")
        print(f"[SLACK MOCK] Title: {title}")
        print(f"[SLACK MOCK] Message: {message}")
        print(f"[SLACK MOCK] Fields: {json.dumps(fields, indent=2) if fields else 'None'}")
        return {"status": "mock_sent"}

    def send_triage_alert(self, client_id: str, domain: str, result: Dict[str, Any]) -> Dict[str, Any]:
        return self.send_alert(
            title=f"Triage Alert: {domain.upper()} | {client_id}",
            message=f"New {domain} triage result processed for {client_id}.",
            severity=result.get("severity", "info"),
            fields={
                "Client": client_id,
                "Domain": domain,
                "Action": result.get("recommended_action", "N/A"),
                "Score": result.get("risk_score", result.get("health_score", "N/A")),
            },
        )
