"""
Pydantic Data Schemas for Month 4: Supply Chain & Logistics Engine
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TransportMode(str, Enum):
    AIR_FREIGHT = "AIR_FREIGHT"
    OCEAN_CONTAINER = "OCEAN_CONTAINER"
    COLD_CHAIN_TRUCK = "COLD_CHAIN_TRUCK"
    LAST_MILE_EXPRESS = "LAST_MILE_EXPRESS"


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LogisticsAction(str, Enum):
    PROCEED_NORMAL = "PROCEED_NORMAL"
    OPTIMIZE_ROUTE = "OPTIMIZE_ROUTE"
    REROUTE_COLD_STORAGE = "REROUTE_COLD_STORAGE"
    ESCALATE_CUSTOMS_DESK = "ESCALATE_CUSTOMS_DESK"
    HOLD_AND_QUARANTINE = "HOLD_AND_QUARANTINE"


class TelemetryData(BaseModel):
    """Real-time IoT sensor telemetry from freight assets."""
    temperature_c: float = Field(..., description="Current sensor temperature in Celsius")
    humidity_percent: float = Field(..., description="Relative humidity percentage")
    shock_g_force: float = Field(..., description="Max shock / impact force detected in Gs")
    location_coords: str = Field(..., description="GPS coordinates (Lat, Long)")


class ShipmentPayload(BaseModel):
    """Incoming shipment manifest and telemetry payload."""
    shipment_id: str = Field(..., description="Unique shipment tracking identifier")
    transport_mode: TransportMode = Field(..., description="Mode of transit")
    carrier: str = Field(..., description="Carrier name")
    origin_country: str = Field(..., description="ISO 2-letter origin country code")
    destination_country: str = Field(..., description="ISO 2-letter destination country code")
    hs_code: str = Field(..., description="Harmonized System tariff classification code")
    declared_temp_range_c: List[float] = Field(..., description="Expected safe temp range [min, max]")
    goods_value_usd: float = Field(..., description="Declared commercial value in USD")
    telemetry: TelemetryData = Field(..., description="Real-time IoT sensor telemetry")
    carrier_status_note: str = Field(..., description="Raw text carrier feed or port status update")


class MitigationStep(BaseModel):
    """Actionable logistics remediation step."""
    step_number: int
    description: str
    requires_human_approval: bool


class LogisticsEvaluationResult(BaseModel):
    """Structured risk assessment output for a shipment."""
    shipment_id: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_tier: RiskTier
    recommended_action: LogisticsAction
    hs_code_valid: bool
    exception_flags: List[str]
    reasoning_trace: str
    mitigation_plan: List[MitigationStep]


class ChainOfCustodyAuditRecord(BaseModel):
    """Immutable chain-of-custody audit ledger entry."""
    log_id: str = Field(..., description="Immutable ledger log ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    shipment_id: str
    event_type: str
    payload_summary: Dict[str, Any]