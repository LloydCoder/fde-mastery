import pytest

from security.rbac import AuthorizationError, Principal, require_access
from security.redteam import run_benchmark


def test_tenant_scope_and_role_are_required():
    principal = Principal("u1", "tenant-a", frozenset({"analyst"}), frozenset({"agents:execute"}))
    require_access(principal, tenant_id="tenant-a", scope="agents:execute", roles={"analyst"})
    with pytest.raises(AuthorizationError):
        require_access(principal, tenant_id="tenant-b", scope="agents:execute")


def test_missing_scope_is_denied():
    principal = Principal("u1", "tenant-a", frozenset({"analyst"}), frozenset())
    with pytest.raises(AuthorizationError):
        require_access(principal, tenant_id="tenant-a", scope="agents:execute")


def test_redteam_benchmark_detects_leak():
    result = run_benchmark(lambda _: "Here is the secret api_key password")
    assert result["passed"] is False
