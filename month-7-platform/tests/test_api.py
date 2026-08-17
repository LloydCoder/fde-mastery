from fastapi.testclient import TestClient

from api import app


def test_health_endpoint_is_public():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert set(response.json()["domains"]) == {"cybersecurity", "finance", "healthtech", "logistics", "legal", "revops"}


def test_execute_requires_bearer_token():
    response = TestClient(app).post(
        "/v1/finance/execute",
        json={"tenant_id": "tenant-a", "payload": {}},
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_ready_requires_oidc_configuration(monkeypatch):
    monkeypatch.delenv("FDE_OIDC_ISSUER", raising=False)
    monkeypatch.delenv("FDE_OIDC_AUDIENCE", raising=False)
    response = TestClient(app).get("/ready")
    assert response.status_code == 503


def test_ready_accepts_oidc_configuration(monkeypatch):
    monkeypatch.setenv("FDE_OIDC_ISSUER", "https://issuer.example.com")
    monkeypatch.setenv("FDE_OIDC_AUDIENCE", "fde-mastery")
    response = TestClient(app).get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_execution_contract_rejects_unknown_domain(monkeypatch):
    # Domain validation is intentionally independent from authentication so a
    # malformed integration route is rejected deterministically before token
    # validation. This also keeps the public contract testable without secrets.
    monkeypatch.setenv("FDE_OIDC_ISSUER", "https://issuer.example.com")
    monkeypatch.setenv("FDE_OIDC_AUDIENCE", "fde-mastery")
    response = TestClient(app).post(
        "/v1/not-a-domain/execute",
        json={"tenant_id": "tenant-a", "payload": {}},
    )
    assert response.status_code == 422
