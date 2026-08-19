"""Pydantic schemas for the SOC Triage Agent."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ThreatCategory(str, Enum):
    AUTHENTICATION = "AUTHENTICATION"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    MALWARE = "MALWARE"
    LATERAL_MOVEMENT = "LATERAL_MOVEMENT"
    RECONNAISSANCE = "RECONNAISSANCE"
    UNKNOWN = "UNKNOWN"


class ActionType(str, Enum):
    AUTO_CONTAIN = "AUTO_CONTAIN"
    ESCALATE_TO_SOC = "ESCALATE_TO_SOC"
    MONITOR = "MONITOR"
    IGNORE_FALSE_POSITIVE = "IGNORE_FALSE_POSITIVE"


class RawSecurityLog(BaseModel):
    """Raw telemetry payload incoming from enterprise SIEM."""
    log_id: str = Field(..., description="Unique ID of the log entry")
    timestamp: datetime = Field(..., description="ISO timestamp of the event")
    source_ip: str = Field(..., description="IP address initiating the activity")
    destination_ip: Optional[str] = Field(None, description="Target IP address")
    user_id: Optional[str] = Field(None, description="User identifier if applicable")
    event_type: str = Field(..., description="Raw event category or action name")
    payload_summary: str = Field(..., description="Unstructured log summary or raw text payload")


class MitigationStep(BaseModel):
    """Specific isolation or containment action recommended by the agent."""
    step_number: int = Field(..., ge=1)
    action: str = Field(..., description="Actionable command (e.g., 'Isolate host host-8831 from network')")
    requires_human_approval: bool = Field(True, description="HITL guardrail indicator")


class ThreatTriageReport(BaseModel):
    """Guaranteed structured output from the LLM Triage Agent."""
    log_id: str
    severity: SeverityLevel
    category: ThreatCategory
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model certainty threshold")
    summary: str = Field(..., description="Executive summary of the threat vectors")
    mitigation_plan: List[MitigationStep] = Field(default_factory=list)
    recommended_action: ActionType
    reasoning_trace: str = Field(..., description="Step-by-step audit log of agent logic")