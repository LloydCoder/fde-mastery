"""Unified platform schemas for Month 7."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class Domain(str, Enum):
    CYBERSECURITY = "cybersecurity"
    FINANCE = "finance"
    HEALTHTECH = "healthtech"
    LOGISTICS = "logistics"
    LEGAL = "legal"
    REVOPS = "revops"


class ClientConfig(BaseModel):
    client_id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    client_name: str
    domains: List[Domain]
    api_tier: str = Field(default="growth", description="starter | growth | enterprise")
    custom_rubric_overrides: Dict[str, Any] = Field(default_factory=dict)
    integration_targets: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class OnboardingResult(BaseModel):
    client_id: str
    status: str = Field(..., description="success | partial | failed")
    schema_mappings: Dict[str, str]
    golden_dataset_path: str
    eval_pass_rate: float
    eval_passed: bool
    deployed_endpoints: List[str]
    logs: List[str] = Field(default_factory=list)


class TriageRequest(BaseModel):
    client_id: str
    domain: Domain
    payload: Dict[str, Any]
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])


class TriageResponse(BaseModel):
    request_id: str
    client_id: str
    domain: str
    result: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    audit_log_id: str


class DriftReport(BaseModel):
    client_id: str
    domain: Domain
    evaluated_at: str
    total_cases: int
    passed: int
    pass_rate: float
    drift_detected: bool
    previous_pass_rate: Optional[float] = None
    delta: Optional[float] = None
    recommendation: str


class BillingRecord(BaseModel):
    client_id: str
    period_start: str
    period_end: str
    total_calls: int
    cost_per_call_usd: float
    total_billed_usd: float
    breakdown_by_domain: Dict[str, int]


class EscalationRecord(BaseModel):
    escalation_id: str
    client_id: str
    domain: Domain
    request_id: str
    reason: str
    human_assigned: Optional[str] = None
    status: str = Field(default="open", description="open | resolved | closed")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None
