"""Adapters exposing Month 1-6 agents through the Month 7 contract."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Type

from pydantic import BaseModel

try:
    from ..schemas import Domain
except ImportError:
    from schemas import Domain

from .domain_agent import DomainAgentResult

ROOT = Path(__file__).resolve().parents[2]


class LegacyAgentLoader:
    """Load a legacy agent without leaving its unqualified schemas module installed."""

    def __init__(self, month_dir: str):
        self.month_dir = ROOT / month_dir
        self._agent_module: ModuleType | None = None
        self.schema_module: ModuleType | None = None

    def load(self) -> ModuleType:
        if self._agent_module is not None:
            return self._agent_module

        package_name = f"fde_legacy_{self.month_dir.name.replace('-', '_')}"
        package = ModuleType(package_name)
        package.__path__ = [str(self.month_dir)]  # type: ignore[attr-defined]
        sys.modules.setdefault(package_name, package)

        schema_path = self.month_dir / "schemas.py"
        if schema_path.exists():
            schema_name = f"{package_name}.schemas"
            schema_spec = importlib.util.spec_from_file_location(schema_name, schema_path)
            if schema_spec is None or schema_spec.loader is None:
                raise ImportError(f"Unable to load legacy schemas: {schema_path}")
            schema_module = importlib.util.module_from_spec(schema_spec)
            sys.modules[schema_name] = schema_module
            self.schema_module = schema_module
            schema_spec.loader.exec_module(schema_module)

        agent_path = self.month_dir / "agent.py"
        if not agent_path.exists():
            raise ImportError(f"Legacy agent not found: {agent_path}")
        agent_name = f"{package_name}.agent"
        spec = importlib.util.spec_from_file_location(agent_name, agent_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load legacy agent: {agent_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[agent_name] = module

        previous = sys.modules.get("schemas")
        if self.schema_module is not None:
            sys.modules["schemas"] = self.schema_module
        try:
            spec.loader.exec_module(module)
        finally:
            if previous is None:
                sys.modules.pop("schemas", None)
            else:
                sys.modules["schemas"] = previous

        self._agent_module = module
        return module


class BaseLegacyAdapter:
    """Normalize legacy agents into the deployment-safe Month 7 contract."""

    domain: Domain
    agent_class_name: str
    payload_class_name: str
    evaluate_method: str
    month_dir: str

    # Actions that can materially affect a person, account, shipment, contract,
    # production system, or customer relationship must remain human-approved.
    HIGH_IMPACT_TOKENS = (
        "AUTO_CONTAIN",
        "AUTO_REJECT",
        "FREEZE",
        "HOLD",
        "QUARANTINE",
        "REROUTE",
        "IMMEDIATE",
        "REJECT",
        "ESCALATE",
        "AMEND",
        "APPROVE",
        "AUTO_ASSIGN",
        "TRIGGER_",
        "FLAG_",
    )

    def __init__(self, *, provider: str | None = None) -> None:
        loader = LegacyAgentLoader(self.month_dir)
        module = loader.load()
        self._module = module
        self._agent_class = getattr(module, self.agent_class_name)
        self._payload_class: Type[BaseModel] | None = getattr(module, self.payload_class_name, None)
        if self._payload_class is None and loader.schema_module is not None:
            self._payload_class = getattr(loader.schema_module, self.payload_class_name, None)
        if self._payload_class is None:
            raise ImportError(f"Payload model {self.payload_class_name} was not found")
        kwargs: Dict[str, Any] = {}
        if provider is not None:
            kwargs["provider"] = provider
        self._agent = self._agent_class(**kwargs)

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        if not isinstance(payload, dict) or not payload:
            raise ValueError(f"{self.domain.value} payload must be a non-empty object")
        model = self._payload_class.model_validate(payload)
        result = getattr(self._agent, self.evaluate_method)(model)
        result_data = result.model_dump(mode="json") if isinstance(result, BaseModel) else {"value": result}
        return DomainAgentResult(
            domain=self.domain,
            result=result_data,
            confidence=self._confidence(result_data),
            requires_human_review=self._requires_review(result_data),
            audit_metadata={
                "adapter": self.__class__.__name__,
                "legacy_agent": self.agent_class_name,
                "deployment_mode": "human_in_the_loop",
            },
        )

    @staticmethod
    def _confidence(result: Dict[str, Any]) -> float:
        for key in ("confidence", "confidence_score"):
            value = result.get(key)
            if isinstance(value, (int, float)):
                numeric = float(value)
                return max(0.0, min(1.0, numeric if numeric <= 1 else numeric / 100.0))
        for key in ("risk_score", "overall_risk_score", "health_score"):
            value = result.get(key)
            if isinstance(value, (int, float)):
                return max(0.0, min(1.0, 1.0 - float(value) / 100.0))
        return 0.5

    @classmethod
    def _requires_review(cls, result: Dict[str, Any]) -> bool:
        action = str(result.get("recommended_action", result.get("action", ""))).upper()
        if any(token in action for token in cls.HIGH_IMPACT_TOKENS):
            return True
        if any(bool(step.get("requires_human_approval")) for step in result.get("mitigation_plan", []) if isinstance(step, dict)):
            return True
        if any(bool(step.get("requires_counsel_approval")) for step in result.get("mitigation_plan", []) if isinstance(step, dict)):
            return True
        return False

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ready",
            "agent": self.agent_class_name,
            "domain": self.domain.value,
            "deployment_mode": "human_in_the_loop",
        }

    def capabilities(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "adapter": self.__class__.__name__,
            "source": self.month_dir,
            "input_model": self.payload_class_name,
            "evaluation_method": self.evaluate_method,
            "human_in_the_loop": True,
        }


class CybersecurityDomainAdapter(BaseLegacyAdapter):
    domain = Domain.CYBERSECURITY
    agent_class_name = "SOCTriageAgent"
    payload_class_name = "RawSecurityLog"
    evaluate_method = "triage_log"
    month_dir = "month-1-cybersecurity"

    def __init__(self) -> None:
        provider = os.getenv("FDE_MONTH1_PROVIDER", "openai")
        if provider == "mock":
            provider = "openai"
        # The legacy agent has its own MOCK_LLM switch; keep deployment explicit.
        super().__init__(provider=provider)


class FinanceDomainAdapter(BaseLegacyAdapter):
    domain = Domain.FINANCE
    agent_class_name = "FinancialRiskAgent"
    payload_class_name = "FinancialTransaction"
    evaluate_method = "evaluate_transaction"
    month_dir = "month-2-finance"


class HealthTechDomainAdapter(BaseLegacyAdapter):
    domain = Domain.HEALTHTECH
    agent_class_name = "HealthTechAgent"
    payload_class_name = "HealthtechPayload"
    evaluate_method = "evaluate_clinical_risk"
    month_dir = "month-3-healthtech"


class LogisticsDomainAdapter(BaseLegacyAdapter):
    domain = Domain.LOGISTICS
    agent_class_name = "LogisticsAgent"
    payload_class_name = "ShipmentPayload"
    evaluate_method = "evaluate"
    month_dir = "month-4-logistics"


class LegalDomainAdapter(BaseLegacyAdapter):
    domain = Domain.LEGAL
    agent_class_name = "LegalAgent"
    payload_class_name = "ContractPayload"
    evaluate_method = "evaluate"
    month_dir = "month-5-legal"


class RevOpsDomainAdapter(BaseLegacyAdapter):
    domain = Domain.REVOPS
    agent_class_name = "RevOpsAgent"
    payload_class_name = "OpportunityPayload"
    evaluate_method = "evaluate"
    month_dir = "month-6-revops"
