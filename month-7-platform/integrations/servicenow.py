"""ServiceNow integration for ticket creation and case management."""

import os
from typing import Any, Dict, Optional


class ServiceNowConnector:
    """Creates and updates ServiceNow incidents for escalated cases."""

    def __init__(
        self,
        instance: str = None,
        username: str = None,
        password: str = None,
    ):
        self.instance = instance or os.environ.get("SERVICENOW_INSTANCE", "")
        self.username = username or os.environ.get("SERVICENOW_USER", "")
        self.password = password or os.environ.get("SERVICENOW_PASS", "")

    def create_incident(
        self,
        short_description: str,
        description: str,
        urgency: str = "3",  # 1=High, 2=Medium, 3=Low
        impact: str = "3",
        caller_id: str = "fde-platform",
        assignment_group: str = "legal-counsel",
    ) -> Dict[str, Any]:
        """Create a ServiceNow incident."""
        payload = {
            "short_description": short_description,
            "description": description,
            "urgency": urgency,
            "impact": impact,
            "caller_id": caller_id,
            "assignment_group": assignment_group,
            "category": "inquiry",
            "subcategory": "internal",
        }

        if self.instance and self.username and self.password:
            try:
                import requests
                url = f"https://{self.instance}.service-now.com/api/now/table/incident"
                resp = requests.post(url, json=payload, auth=(self.username, self.password), timeout=10)
                return {"status": "created", "ticket_number": resp.json().get("result", {}).get("number"), "code": resp.status_code}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        print(f"[SERVICENOW MOCK] Incident created:")
        print(f"  Short: {short_description}")
        print(f"  Desc:  {description}")
        print(f"  Urgency: {urgency} | Impact: {impact}")
        return {"status": "mock_created", "ticket_number": f"INC-MOCK-{hash(short_description) % 100000}"}

    def create_escalation_ticket(self, client_id: str, domain: str, reason: str) -> Dict[str, Any]:
        return self.create_incident(
            short_description=f"[{domain.upper()}] Escalation for {client_id}",
            description=f"Automated escalation triggered. Reason: {reason}",
            urgency="2",
            impact="2",
            assignment_group=f"{domain}-team",
        )