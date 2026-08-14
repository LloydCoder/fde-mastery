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
