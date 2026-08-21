from fastapi.testclient import TestClient

from deployment.api_gateway.main import app


def test_v1_health_is_versioned() -> None:
    response = TestClient(app).get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "api_version": "v1"}


def test_openapi_contains_v1_contract() -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3.1")
    assert "/v1/health" in schema["paths"]
    assert "/v1/capabilities" in schema["paths"]
    assert "/v1/triage/{client_id}/{domain}" in schema["paths"]


def test_v1_capabilities_requires_authentication() -> None:
    response = TestClient(app).get("/v1/capabilities")
    assert response.status_code in {401, 403}
