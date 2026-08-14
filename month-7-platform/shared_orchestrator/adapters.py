"""Adapters that expose the real Month 1-6 agents through one platform contract.

The monthly projects intentionally remain independently runnable. This module
loads those legacy modules by path and translates their domain-specific Pydantic
models into the Month 7 ``DomainAgentResult`` envelope.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Tuple, Type

from pydantic import BaseModel

from .domain_agent import DomainAgentResult
from ..schemas import Domain

ROOT = Path(__file__).resolve().parents[2]


class LegacyAgentLoader:
    """Load an existing monthly agent without requiring the hyphenated folder to be a package."""

    def __init__(self, month_dir: str):
        self.month_dir = ROOT / month_dir
        self._agent_module: ModuleType | None = None

    def load(self) -> ModuleType:
        if self._agent_module is not None:
            return self._agent_module

        package_name = f"fde_legacy_{self.month_dir.name.replace('-', '_')}"
        package = ModuleType(package_name)
        package.__path__ = [str(self.month_dir)]  # type: ignore[attr-defined]
        sys.modules.setdefault(package_name, package)

        agent_path = self.month_dir / "agent.py"
        if not agent_path.exists():
            raise ImportError(f"Legacy agent not found: {agent_path}")

        spec = importlib.util.spec_from_file_location(
            f"{package_name}.agent", agent_path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load legacy agent: {agent_path}")

        # Months 1, 2 and 4 use ``from schemas import ...``. Temporarily expose
        # their local schemas during module execution, then restore the previous
        # global module so different monthly agents cannot permanently collide.
        schema_path = self.month_dir / "schemas.py"
        previous_schema = sys.modules.get("schemas")
        if schema_path.exists():
            schema_spec = importlib.util.spec_from_file_location(
                f"{package_name}.schemas", schema_path
            )
            if schema_spec is None or schema_spec.loader is None:
                raise ImportError(f"Unable to load legacy schemas: {schema_path}")
            schema_module = importlib.util.module_from_spec(schema_spec)
            sys.modules[f"{package_name}.schemas"] = schema_module
            sys.modules["schemas"] = schema_module
            schema_spec.loader.exec_module(schema_module)

        try:
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            self._agent_module = module
            return module
        finally:
            if previous_schema is None:
                sys.modules.pop("schemas", None)
            else:
                sys.modules["schemas"] = previous_schema


class BaseLegacyAdapter:
    domain: Domain
    agent_class_name: str
    payload_class_name: str
    evaluate_method: str
    month_dir: str

    def __init__(self) -> None:
        module = LegacyAgentLoader(self.month_dir).load()
        self._module = module
        self._agent_class = getattr(module, self.agent_class_name)
        self._payload_class: Type[BaseModel] = getattr(module, self.payload_class_name, None)  # type: ignore[assignment]
        if self._payload_class is None:
            # Payload schemas live in the monthly schemas module rather than agent.py.
            package_name = f"fde_legacy_{Path(self.month_dir).name.replace('-', '_')}"
            schema_module = sys.modules.get(f"{package_name}.schemas")
            if schema_module is None:
                raise ImportError(f"Unable to locate schema module for {self.month_dir}")
            self._payload_class = getattr(schema_module, self.payload_class_name)
        self._agent = self._agent_class()

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        model = self._payload_class.model_validate(payload)
        result = getattr(self._agent, self.evaluate_method)(model)
        result_data = result.model_dump(mode="json") if isinstance(result, BaseModel) else {"value": result}
        confidence = self._confidence(result_data)
        return DomainAgentResult(
            domain=self.domain,
            result=result_data,
            confidence=confidence,
            requires_human_review=self._requires_review(result_data),
            audit_metadata={"adapter": self.__class__.__name__, "legacy_agent": self.agent_class_name},
        )

    def _confidence(self, result: Dict[str, Any]) -> float:
        for key in ("confidence", "confidence_score"):
            value = result.get(key)
            if isinstance(value, (int, float)):
                return max(0.0, min(1.0, float(value) if float(value) <= 1 else float(value) / 100.0))
        return 0.5

    def _requires_review(self, result: Dict[str, Any]) -> bool:
        action = str(result.get("recommended_action", result.get("action", ""))).upper()
        return any(token in action for token in ("REVIEW", "ESCALATE", "REJECT", "FREEZE", "HOLD"))

    def health(self) -> Dict[str, Any]:
        return {"status": "ready", "agent": self.agent_class_name, "domain": self.domain.value}

    def capabilities(self) -> Dict[str, Any]:
        return {"domain": self.domain.value, "adapter": self.__class__.__name__, "source": self.month_dir}


class CybersecurityDomainAdapter(BaseLegacyAdapter):
    domain = Domain.CYBERSECURITY
    agent_class_name = "SOCTriageAgent"
    payload_class_name = "RawSecurityLog"
    evaluate_method = "triage_log"
    month_dir = "month-1-cybersecurity"

    def __init__(self) -> None:
        # Month 1 defaults to a live provider. Platform tests and local demos stay deterministic.
        self._module = LegacyAgentLoader(self.month_dir).load()
        self._agent_class = getattr(self._module, self.agent_class_name)
        schema_module = sys.modules.get("schemas")
        self._payload_class = getattr(schema_module, self.payload_class_name)
        self._agent = self._agent_class(provider="openai")


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
