"""Tests for platform-level operational architecture."""

import importlib.util
import os
import sys
from pathlib import Path

os.environ.setdefault("FDE_API_KEYS", "test-api-key")
os.environ.setdefault("FDE_ADMIN_API_KEYS", "test-admin-key")
os.environ.setdefault("FDE_STORAGE_BACKEND", "memory")
os.environ.setdefault("FDE_RATE_LIMIT_BACKEND", "memory")
os.environ.setdefault("MOCK_LLM", "true")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("fde_architecture_api", ROOT / "deployment/api_gateway/main.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(module.app)


def test_readiness_is_available():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_metrics_requires_authentication():
    assert client.get("/metrics").status_code == 401


def test_metrics_exposes_prometheus_format():
    response = client.get("/metrics", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    assert "# TYPE fde_http_requests_total counter" in response.text


def test_security_headers_are_present():
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Request-ID"]
