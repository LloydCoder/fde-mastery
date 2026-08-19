"""Canonical domain adapters for the enterprise platform."""

from ._legacy import BaseLegacyAdapter
from .cybersecurity import CybersecurityDomainAdapter
from .finance import FinanceDomainAdapter
from .healthtech import HealthTechDomainAdapter
from .logistics import LogisticsDomainAdapter
from .legal import LegalDomainAdapter
from .revops import RevOpsDomainAdapter
from .procurement import ProcurementDomainAdapter

__all__ = [
    "BaseLegacyAdapter",
    "CybersecurityDomainAdapter",
    "FinanceDomainAdapter",
    "HealthTechDomainAdapter",
    "LogisticsDomainAdapter",
    "LegalDomainAdapter",
    "RevOpsDomainAdapter",
    "ProcurementDomainAdapter",
]
