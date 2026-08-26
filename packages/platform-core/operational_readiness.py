"""Deterministic production-readiness checks for the platform boundary.

The readiness contract deliberately checks configuration and platform invariants,
not remote dependency health. Liveness and dependency probes belong to the
runtime/deployment layer so a transient database or Redis outage does not turn
configuration readiness into an opaque application failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from config import Settings


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    ready: bool
    detail: str


@dataclass(frozen=True)
class OperationalReadiness:
    ready: bool
    checks: tuple[ReadinessCheck, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "ready" if self.ready else "not_ready",
            "checks": [
                {"name": check.name, "ready": check.ready, "detail": check.detail}
                for check in self.checks
            ],
        }


def assess_readiness(settings: Settings, configured_domains: set[str], expected_domains: set[str]) -> OperationalReadiness:
    """Evaluate non-secret production invariants without making network calls."""
    checks: list[ReadinessCheck] = []

    try:
        settings.validate()
        checks.append(ReadinessCheck("runtime_configuration", True, "validated"))
    except ValueError as exc:
        checks.append(ReadinessCheck("runtime_configuration", False, str(exc)))

    checks.append(
        ReadinessCheck(
            "persistent_storage",
            settings.environment != "production" or settings.storage_backend == "postgres",
            "postgres required in production" if settings.environment == "production" else settings.storage_backend,
        )
    )
    checks.append(
        ReadinessCheck(
            "distributed_rate_limiting",
            settings.environment != "production" or settings.rate_limit_backend == "redis",
            "redis required in production" if settings.environment == "production" else settings.rate_limit_backend,
        )
    )
    checks.append(
        ReadinessCheck(
            "managed_secrets",
            settings.environment != "production" or settings.secrets_backend == "managed",
            "managed secrets required in production" if settings.environment == "production" else settings.secrets_backend,
        )
    )
    checks.append(
        ReadinessCheck(
            "oidc",
            settings.environment != "production" or bool(settings.oidc_issuer and settings.oidc_audience),
            "issuer and audience required in production" if settings.environment == "production" else "not required outside production",
        )
    )
    checks.append(
        ReadinessCheck(
            "mock_model_disabled",
            settings.environment != "production" or not settings.mock_llm,
            "MOCK_LLM must be disabled in production" if settings.environment == "production" else "not required outside production",
        )
    )
    checks.append(
        ReadinessCheck(
            "domain_router",
            configured_domains == expected_domains,
            "domain set matches canonical contract" if configured_domains == expected_domains else "domain router does not match canonical contract",
        )
    )

    return OperationalReadiness(ready=all(check.ready for check in checks), checks=tuple(checks))
