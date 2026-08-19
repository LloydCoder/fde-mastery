"""
Pydantic Data Schemas for Month 3: HealthTech Data Engineering & HIPAA Pipelines
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class ClinicalRiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AutomatedTriageAction(str, Enum):
    ROUTINE_CARE = "ROUTINE_CARE"
    MONITOR_PATIENT = "MONITOR_PATIENT"
    ESCALATE_TO_PHYSICIAN = "ESCALATE_TO_PHYSICIAN"
    IMMEDIATE_INTERVENTION = "IMMEDIATE_INTERVENTION"


class HealthtechPayload(BaseModel):
    """Incoming clinical encounter payload for triage and PHI processing."""
    encounter_id: str
    patient_id: str
    encounter_type: str  # e.g., "AMBULATORY", "EMERGENCY", "INPATIENT"
    primary_symptom: str
    vital_signs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Vitals: heart_rate, systolic_bp, diastolic_bp, temp_c, spo2"
    )
    raw_notes: str
    phi_redacted: bool = False


class PHIDeidentificationReport(BaseModel):
    """HIPAA Safe Harbor de-identification output."""
    original_length: int
    redacted_text: str
    identifiers_detected: List[str]  # e.g., ["NAME", "SSN", "DOB", "PHONE"]
    compliance_standard: str = "HIPAA_SAFE_HARBOR"


class ClinicalAnalyticsReport(BaseModel):
    """Structured clinical risk assessment output."""
    encounter_id: str
    risk_score: float = Field(ge=0.0, le=100.0)
    severity: ClinicalRiskTier
    action: AutomatedTriageAction
    reasoning_trace: str
    icd10_codes: List[str] = Field(default_factory=list)
    snomed_codes: List[str] = Field(default_factory=list)
    automation_steps: List[str] = Field(default_factory=list)


class HITECHAuditLedgerEntry(BaseModel):
    """Immutable audit entry for compliance logging."""
    log_id: str
    timestamp: str
    encounter_id: str
    patient_hash: str
    event_type: str
    phi_redacted: bool
    payload_summary: Dict[str, Any]