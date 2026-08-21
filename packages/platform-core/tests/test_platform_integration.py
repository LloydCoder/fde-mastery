from datetime import datetime, timezone

# Existing platform integration tests intentionally retain their original application fixture.
# Only the promoted domain set changes in Build 13.


def test_unknown_client_is_rejected(client):
    response = client.post("/api/missing/finance/triage", json=DOMAIN_CASES[1][1], headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 404


def test_usage_is_persisted_through_repository(client):
    response = client.post("/api/test-client/finance/triage", json=DOMAIN_CASES[1][1], headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200, response.text
    assert module.REPOSITORY.get_usage("test-client") == 1


def test_agent_health_exposes_all_domains(client):
    response = client.get("/health/agents", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    assert set(response.json()) == {"cybersecurity", "finance", "healthtech", "logistics", "legal", "revops", "procurement", "custom"}
