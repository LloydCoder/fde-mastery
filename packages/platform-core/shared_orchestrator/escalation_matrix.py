"""Human handoff protocols for high-risk or ambiguous cases."""

from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from ..schemas import Domain, EscalationRecord
except ImportError:
    from schemas import Domain, EscalationRecord


class EscalationMatrix:
    """Manages human escalation for cases that exceed autonomous thresholds."""

    def __init__(self):
        self._escalations: Dict[str, EscalationRecord] = {}

    def escalate(
        self,
        client_id: str,
        domain: Domain,
        request_id: str,
        reason: str,
        human_assigned: Optional[str] = None,
    ) -> EscalationRecord:
        esc_id = f"ESC-{request_id}"
        record = EscalationRecord(
            escalation_id=esc_id,
            client_id=client_id,
            domain=domain,
            request_id=request_id,
            reason=reason,
            human_assigned=human_assigned,
            status="open",
        )
        self._escalations[esc_id] = record
        return record

    def resolve(self, escalation_id: str, resolution: str) -> Optional[EscalationRecord]:
        record = self._escalations.get(escalation_id)
        if record:
            record.status = "resolved"
            record.resolved_at = datetime.now().isoformat()
        return record

    def list_open(self, client_id: Optional[str] = None) -> List[EscalationRecord]:
        records = [r for r in self._escalations.values() if r.status == "open"]
        if client_id:
            records = [r for r in records if r.client_id == client_id]
        return records