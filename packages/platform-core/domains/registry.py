"""Canonical registry for first-class FDE domains.

The registry owns domain metadata and lazy implementation loading. The kernel
only consumes the provider-neutral descriptor contract; implementation imports
remain outside the kernel boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable

from fde_platform.contracts.domain import DomainDescriptor


@dataclass(frozen=True, slots=True)
class DomainRegistration:
    descriptor: DomainDescriptor
    factory: str
    fixture_key: str

    def validate_metadata(self) -> None:
        self.descriptor.validate()
        if not self.factory or ":" not in self.factory:
            raise ValueError(f"invalid domain factory: {self.factory!r}")
        if not self.fixture_key.strip():
            raise ValueError("fixture_key is required")

    def load_factory(self) -> Callable[[], Any]:
        self.validate_metadata()
        module_name, attribute = self.factory.split(":", 1)
        module = import_module(module_name)
        factory = getattr(module, attribute, None)
        if factory is None or not callable(factory):
            raise TypeError(f"domain factory is not callable: {self.factory}")
        return factory

    def instantiate(self) -> Any:
        return self.load_factory()()


_COMMON_EVAL = "golden_datasets/domain_smoke_cases.json"


def _registration(
    domain_id: str,
    display_name: str,
    factory: str,
    capabilities: tuple[str, ...],
    *,
    source: str,
    risk_level: str = "medium",
    lifecycle_stage: str = "pilot",
) -> DomainRegistration:
    return DomainRegistration(
        descriptor=DomainDescriptor(
            domain_id=domain_id,
            display_name=display_name,
            version="1.0.0",
            capabilities=capabilities,
            lifecycle_stage=lifecycle_stage,
            risk_level=risk_level,
            human_approval_required=True,
            evaluation_suite="tests/test_domain_promotion.py",
            representative_dataset=_COMMON_EVAL,
            source=source,
        ),
        factory=factory,
        fixture_key=domain_id,
    )


DOMAIN_CATALOG: dict[str, DomainRegistration] = {
    "cybersecurity": _registration(
        "cybersecurity", "Cybersecurity", "shared_orchestrator.adapters:CybersecurityDomainAdapter",
        ("security_triage", "risk_classification", "incident_recommendation"),
        source="legacy-month-1-compatible",
        risk_level="high",
    ),
    "finance": _registration(
        "finance", "Finance", "shared_orchestrator.adapters:FinanceDomainAdapter",
        ("transaction_risk", "fraud_risk", "financial_recommendation"),
        source="legacy-month-2-compatible",
        risk_level="high",
    ),
    "healthtech": _registration(
        "healthtech", "HealthTech", "shared_orchestrator.adapters:HealthTechDomainAdapter",
        ("clinical_risk", "patient_safety", "care_recommendation"),
        source="legacy-month-3-compatible",
        risk_level="critical",
    ),
    "logistics": _registration(
        "logistics", "Logistics", "shared_orchestrator.adapters:LogisticsDomainAdapter",
        ("shipment_risk", "exception_detection", "routing_recommendation"),
        source="legacy-month-4-compatible",
        risk_level="high",
    ),
    "legal": _registration(
        "legal", "Legal", "shared_orchestrator.adapters:LegalDomainAdapter",
        ("contract_analysis", "legal_risk", "clause_recommendation"),
        source="legacy-month-5-compatible",
        risk_level="high",
    ),
    "revops": _registration(
        "revops", "Revenue Operations", "shared_orchestrator.adapters:RevOpsDomainAdapter",
        ("opportunity_risk", "pipeline_analysis", "commercial_recommendation"),
        source="legacy-month-6-compatible",
        risk_level="medium",
    ),
    "procurement": _registration(
        "procurement", "Procurement", "domains.procurement.agent:ProcurementAgent",
        ("supplier_risk", "quote_comparison", "spend_thresholds"),
        source="native-v1",
        risk_level="high",
        lifecycle_stage="production",
    ),
    "custom": _registration(
        "custom", "Custom", "domains.custom.agent:CustomDomainAgent",
        ("classification", "recommendation", "configuration_driven"),
        source="native-v1",
        risk_level="medium",
    ),
}


def get_domain_registration(domain_id: str) -> DomainRegistration:
    """Return a validated registration or fail closed for unknown domains."""
    key = domain_id.strip().lower()
    try:
        registration = DOMAIN_CATALOG[key]
    except KeyError as exc:
        raise KeyError(f"unknown domain: {domain_id}") from exc
    registration.validate_metadata()
    return registration


def validate_catalog() -> None:
    """Validate the static catalog without importing provider implementations."""
    if not DOMAIN_CATALOG:
        raise ValueError("domain catalog cannot be empty")
    for registration in DOMAIN_CATALOG.values():
        registration.validate_metadata()
    if len(DOMAIN_CATALOG) != len(set(DOMAIN_CATALOG)):
        raise ValueError("domain identifiers must be unique")
