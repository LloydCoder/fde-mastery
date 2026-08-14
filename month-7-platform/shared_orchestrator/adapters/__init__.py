"""Adapters exposing Month 1-6 domain agents through the Month 7 contract."""

from .cybersecurity import CybersecurityDomainAdapter
from .finance import FinanceDomainAdapter
from .healthtech import HealthTechDomainAdapter
from .logistics import LogisticsDomainAdapter
from .legal import LegalDomainAdapter
from .revops import RevOpsDomainAdapter

__all__ = [
    "CybersecurityDomainAdapter",
    "FinanceDomainAdapter",
    "HealthTechDomainAdapter",
    "LogisticsDomainAdapter",
    "LegalDomainAdapter",
    "RevOpsDomainAdapter",
]
