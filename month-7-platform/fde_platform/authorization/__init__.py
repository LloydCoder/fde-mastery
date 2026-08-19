"""Authorization primitives: explicit resource context plus fail-closed decisions."""

from .policy import AuthorizationDecision, AuthorizationRequest, Policy
from .service import AuthorizationService, DefaultAuthorizationService

__all__ = [
    "AuthorizationDecision",
    "AuthorizationRequest",
    "AuthorizationService",
    "DefaultAuthorizationService",
    "Policy",
]
