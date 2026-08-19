"""Domain plugin metadata contracts."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True, slots=True)
class DomainDescriptor:
    """Describes a domain without coupling the platform to its implementation."""

    domain_id: str
    display_name: str
    version: str
    capabilities: Tuple[str, ...] = ()
