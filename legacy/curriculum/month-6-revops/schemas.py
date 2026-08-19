"""Pydantic schemas for RevOps & Enterprise Automation Engine."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LeadSource(str, Enum):
    PRODUCT_QUALIFIED_PQL = "PRODUCT_QUALIFIED_PQL"
    INBOUND_DEMO = "INBOUND_DEMO"
    OUTBOUND_EXEC_OUTREACH = "OUTBOUND_EXEC_OUTREACH"
    ORGANIC_SEARCH = "ORGANIC_SEARCH"


class DealStage(str, Enum):
    QUALIFICATION = "QUALIFICATION"
    TECHNICAL_EVALUATION = "TECHNICAL_EVALUATION"
    PROPOSAL_NEGOTIATION = "PROPOSAL_NEGOTIATION"
    CLOSED_WON = "CLOSED_WON"


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RevOpsAction(str, Enum):
    AUTO_ASSIGN_ENTERPRISE_AE = "AUTO_ASSIGN_ENTERPRISE_AE"
    ESCALATE_DEAL_DESK = "ESCALATE_DEAL_DESK"
    FLAG_CHURN_RISK = "FLAG_CHURN_RISK"
    TRIGGER_ENRICHMENT_NURTURE = "TRIGGER_ENRICHMENT_NURTURE"


class TelemetryMetrics(BaseModel):
    monthly_active_users: int = Field(..., description="Active user count in platform")
    weekly_usage_growth_pct: float = Field(..., description="Week-over-week platform usage delta %")
    license_utilization_pct: float = Field(..., description="Percentage of seat licenses utilized")


class OpportunityPayload(BaseModel):
    opportunity_id: str = Field(..., description="Unique CRM opportunity/deal ID")
    account_name: str = Field(..., description="Target enterprise account name")
    annual_recurring_revenue_usd: float = Field(..., description="ARR impact in USD")
    lead_source: LeadSource = Field(..., description="Primary lead acquisition channel")
    deal_stage: DealStage = Field(..., description="Current sales pipeline stage")
    discount_requested_pct: float = Field(..., description="Requested contract discount %")
    has_exec_sponsor: bool = Field(..., description="Is executive sponsor engaged")
    telemetry: TelemetryMetrics = Field(..., description="Product usage telemetry")


class AutomationStep(BaseModel):
    step_number: int
    system_target: str
    action_description: str
    is_automated: bool


class RevOpsEvaluationResult(BaseModel):
    opportunity_id: str
    health_score: float = Field(..., ge=0.0, le=100.0)
    risk_tier: RiskTier
    recommended_action: RevOpsAction
    exception_flags: List[str]
    reasoning_trace: str
    automation_workflow: List[AutomationStep]


class RevOpsAuditRecord(BaseModel):
    log_id: str = Field(..., description="Immutable audit record hash")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    opportunity_id: str
    event_type: str
    summary: Dict[str, Any]