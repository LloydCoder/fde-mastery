"""Pydantic schemas for Legal Tech & Contract Risk Analysis Engine."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ClauseType(str, Enum):
    LIABILITY_CAP = "LIABILITY_CAP"
    INDEMNIFICATION = "INDEMNIFICATION"
    GOVERNING_LAW = "GOVERNING_LAW"
    IP_ASSIGNMENT = "IP_ASSIGNMENT"
    TERMINATION = "TERMINATION"
    DATA_PRIVACY_GDPR = "DATA_PRIVACY_GDPR"


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LegalAction(str, Enum):
    APPROVE_STANDARD = "APPROVE_STANDARD"
    AMEND_CLAUSE = "AMEND_CLAUSE"
    ESCALATE_LEGAL_COUNSEL = "ESCALATE_LEGAL_COUNSEL"
    REJECT_CONTRACT = "REJECT_CONTRACT"


class ContractClause(BaseModel):
    clause_id: str = Field(..., description="Unique section/clause identifier")
    clause_type: ClauseType = Field(..., description="Categorized clause taxonomy")
    section_title: str = Field(..., description="Section title or heading")
    text: str = Field(..., description="Verbatim clause text")


class ContractPayload(BaseModel):
    contract_id: str = Field(..., description="Unique contract identifier")
    title: str = Field(..., description="Title of agreement")
    counterparty: str = Field(..., description="Counterparty organization name")
    governing_jurisdiction: str = Field(..., description="State or legal jurisdiction specified")
    annual_contract_value_usd: float = Field(..., description="Total annual value in USD")
    clauses: List[ContractClause] = Field(..., description="List of extracted contractual clauses")


class ClauseRedline(BaseModel):
    clause_id: str
    original_text: str
    proposed_redline: str
    risk_reasoning: str


class LegalMitigationStep(BaseModel):
    step_number: int
    description: str
    requires_counsel_approval: bool


class LegalEvaluationResult(BaseModel):
    contract_id: str
    overall_risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_tier: RiskTier
    recommended_action: LegalAction
    exception_flags: List[str]
    proposed_redlines: List[ClauseRedline]
    reasoning_trace: str
    mitigation_plan: List[LegalMitigationStep]


class LegalAuditRecord(BaseModel):
    log_id: str = Field(..., description="Immutable legal audit record ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    contract_id: str
    event_type: str
    summary: Dict[str, Any]