import pytest

from fde_platform.authorization.service import DefaultAuthorizationService
from fde_platform.control_plane import (
    ControlPlaneResource,
    CustomerControlPlane,
    CustomerEnvironment,
    CustomerProject,
    ResourceKind,
)
from fde_platform.identity import Environment, Principal, PrincipalType, RequestContext, TenantId, TenantRef


def context(tenant: str = "tenant-a") -> RequestContext:
    tenant_id = TenantId(tenant)
    tenant_ref = TenantRef(tenant_id, Environment.PRODUCTION)
    principal = Principal("user-1", tenant_id, PrincipalType.USER, roles=frozenset({"admin"}))
    return RequestContext(principal, tenant_ref, "req-1", Environment.PRODUCTION)


def test_customer_control_plane_enforces_environment_project_resource_hierarchy():
    plane = CustomerControlPlane(DefaultAuthorizationService())
    ctx = context()
    plane.register_environment(ctx, CustomerEnvironment("prod", "tenant-a", "Production", production=True))
    plane.register_project(ctx, CustomerProject("project-a", "tenant-a", "prod", "Core AI"))
    resource = plane.register_resource(
        ctx,
        ControlPlaneResource("agent-a", "tenant-a", "project-a", ResourceKind.AGENT, "Agent A"),
    )
    assert plane.get_resource(ctx, "agent-a", ResourceKind.AGENT) == resource
    snapshot = plane.snapshot(ctx)
    assert [item.environment_id for item in snapshot.environments] == ["prod"]
    assert [item.project_id for item in snapshot.projects] == ["project-a"]
    assert [item.resource_id for item in snapshot.resources] == ["agent-a"]


def test_project_requires_existing_environment():
    plane = CustomerControlPlane(DefaultAuthorizationService())
    with pytest.raises(KeyError, match="environment not found"):
        plane.register_project(context(), CustomerProject("project-a", "tenant-a", "missing", "Core AI"))


def test_resource_requires_existing_project():
    plane = CustomerControlPlane(DefaultAuthorizationService())
    with pytest.raises(KeyError, match="project not found"):
        plane.register_resource(
            context(),
            ControlPlaneResource("agent-a", "tenant-a", "missing", ResourceKind.AGENT, "Agent A"),
        )


def test_cross_tenant_registration_is_denied_by_existing_authorization_boundary():
    plane = CustomerControlPlane(DefaultAuthorizationService())
    with pytest.raises(PermissionError):
        plane.register_environment(
            context("tenant-a"),
            CustomerEnvironment("prod", "tenant-b", "Production", production=True),
        )


def test_cross_tenant_resources_are_not_visible_in_snapshot():
    plane = CustomerControlPlane(DefaultAuthorizationService())
    plane.register_environment(context("tenant-a"), CustomerEnvironment("prod-a", "tenant-a", "A"))
    plane.register_project(context("tenant-a"), CustomerProject("project-a", "tenant-a", "prod-a", "A"))
    plane.register_environment(context("tenant-b"), CustomerEnvironment("prod-b", "tenant-b", "B"))
    plane.register_project(context("tenant-b"), CustomerProject("project-b", "tenant-b", "prod-b", "B"))
    plane.register_resource(
        context("tenant-a"), ControlPlaneResource("agent-a", "tenant-a", "project-a", ResourceKind.AGENT, "A"),
    )
    plane.register_resource(
        context("tenant-b"), ControlPlaneResource("agent-b", "tenant-b", "project-b", ResourceKind.AGENT, "B"),
    )
    snapshot = plane.snapshot(context("tenant-a"))
    assert snapshot.tenant_id == "tenant-a"
    assert {item.resource_id for item in snapshot.resources} == {"agent-a"}
    with pytest.raises(KeyError):
        plane.get_resource(context("tenant-a"), "agent-b", ResourceKind.AGENT)
