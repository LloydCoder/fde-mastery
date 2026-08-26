from config import Settings
from operational_readiness import assess_readiness


def production_settings(**overrides) -> Settings:
    values = {
        "environment": "production",
        "storage_backend": "postgres",
        "database_url": "postgresql+psycopg://fde:test@localhost/fde",
        "rate_limit_backend": "redis",
        "redis_url": "redis://localhost:6379/0",
        "secrets_backend": "managed",
        "oidc_issuer": "https://issuer.example.test",
        "oidc_audience": "fde-mastery",
        "mock_llm": False,
    }
    values.update(overrides)
    return Settings(**values)


def test_production_readiness_requires_all_operational_invariants():
    domains = {"cybersecurity", "finance", "healthtech", "logistics", "legal", "revops", "procurement", "custom"}
    result = assess_readiness(production_settings(), domains, domains)

    assert result.ready is True
    assert {check.name for check in result.checks} == {
        "runtime_configuration",
        "persistent_storage",
        "distributed_rate_limiting",
        "managed_secrets",
        "oidc",
        "mock_model_disabled",
        "domain_router",
    }


def test_production_readiness_fails_closed_for_memory_storage():
    result = assess_readiness(
        production_settings(storage_backend="memory", database_url=None),
        {"cybersecurity"},
        {"cybersecurity"},
    )

    assert result.ready is False
    assert any(not check.ready and check.name == "persistent_storage" for check in result.checks)


def test_production_readiness_fails_closed_for_mock_model():
    result = assess_readiness(
        production_settings(mock_llm=True),
        {"cybersecurity"},
        {"cybersecurity"},
    )

    assert result.ready is False
    assert any(not check.ready and check.name == "mock_model_disabled" for check in result.checks)


def test_readiness_does_not_treat_partial_domain_router_as_ready():
    domains = {"cybersecurity", "finance"}
    result = assess_readiness(production_settings(), domains, {"cybersecurity", "finance", "custom"})

    assert result.ready is False
    assert any(not check.ready and check.name == "domain_router" for check in result.checks)
