"""Customer control-plane contracts and service.

The control plane provides one tenant-scoped view over customer environments, projects,
agents, workflows, integrations, evaluations and deployments. It delegates authorization
to the existing authorization service and never implements a second policy engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Generic, TypeVar

from fde_platform.authorization.policy import AuthorizationRequest
from fde_platform.authorization.service import AuthorizationService
from fde_platform.identity.context import RequestContext


class ResourceKind(StrEnum):
    ENVIRONMENT = "environment"
    PROJECT = "project"
    AGENT = "agent"
    WORKFLOW = "workflow"
    TOOL = "tool"
    MODEL = "model"
    POLICY = "policy"
    INTEGRATION = "integration"
    EVALUATION = "evaluation"
    DEPLOYMENT = "deployment"
    INCIDENT = "incident"


@dataclass(frozen=True, slots=True)
class CustomerEnvironment:
    environment_id: str
    tenant_id: str
    name: str
    production: bool = False

    def __post_init__(self) -> None:
        if not self.environment_id.strip() or not self.tenant_id.strip() or not self.name.strip():
            raise ValueError("environment identity and name are required")


@dataclass(frozen=True, slots=True)
class CustomerProject:
    project_id: str
    tenant_id: str
    environment_id: str
    name: str

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.project_id, self.tenant_id, self.environment_id, self.name)):
            raise ValueError("project identity, tenant and environment are required")


@dataclass(frozen=True, slots=True)
class ControlPlaneResource:
    resource_id: str
    tenant_id: str
    project_id: str
    kind: ResourceKind
    name: str
    version: int = 1
    state: str = "active"
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.resource_id, self.tenant_id, self.project_id, self.name)):
            raise ValueError("resource identity, tenant, project and name are required")
        if self.version < 1:
            raise ValueError("resource version must be positive")
        if self.state not in {"draft", "staged", "shadow", "active", "retired"}:
            raise ValueError("invalid resource state")


@dataclass(frozen=True, slots=True)
class ControlPlaneSnapshot:
    tenant_id: str
    environments: tuple[CustomerEnvironment, ...]
    projects: tuple[CustomerProject, ...]
    resources: tuple[ControlPlaneResource, ...]


T = TypeVar("T")


class CustomerControlPlane(Generic[T]):
    """Tenant-scoped customer inventory backed by the existing authorization boundary."""

    def __init__(self, authorization: AuthorizationService) -> None:
        self._authorization = authorization
        self._environments: dict[tuple[str, str], CustomerEnvironment] = {}
        self._projects: dict[tuple[str, str], CustomerProject] = {}
        self._resources: dict[tuple[str, str], ControlPlaneResource] = {}

    def _require(self, context: RequestContext, action: str, resource: str, resource_tenant_id: str) -> None:
        self._authorization.require(
            AuthorizationRequest(
                context=context,
                action=action,
                resource=resource,
                resource_tenant_id=resource_tenant_id,
            )
        )

    def register_environment(self, context: RequestContext, environment: CustomerEnvironment) -> CustomerEnvironment:
        self._require(context, "control_plane.environment.write", "environment", environment.tenant_id)
        key = (environment.tenant_id, environment.environment_id)
        if key in self._environments:
            raise ValueError("environment already exists")
        self._environments[key] = environment
        return environment

    def register_project(self, context: RequestContext, project: CustomerProject) -> CustomerProject:
        self._require(context, "control_plane.project.write", "project", project.tenant_id)
        if (project.tenant_id, project.environment_id) not in self._environments:
            raise KeyError("environment not found")
        key = (project.tenant_id, project.project_id)
        if key in self._projects:
            raise ValueError("project already exists")
        self._projects[key] = project
        return project

    def register_resource(self, context: RequestContext, resource: ControlPlaneResource) -> ControlPlaneResource:
        self._require(context, f"control_plane.{resource.kind}.write", resource.kind.value, resource.tenant_id)
        if (resource.tenant_id, resource.project_id) not in self._projects:
            raise KeyError("project not found")
        key = (resource.tenant_id, resource.resource_id)
        if key in self._resources:
            raise ValueError("resource already exists")
        self._resources[key] = resource
        return resource

    def get_resource(self, context: RequestContext, resource_id: str, kind: ResourceKind) -> ControlPlaneResource:
        resource = self._resources.get((context.tenant_id, resource_id))
        if resource is None or resource.kind is not kind:
            raise KeyError("resource not found")
        self._require(context, f"control_plane.{kind}.read", kind.value, resource.tenant_id)
        return resource

    def snapshot(self, context: RequestContext) -> ControlPlaneSnapshot:
        self._require(context, "control_plane.snapshot.read", "control_plane", context.tenant_id)
        tenant_id = str(context.tenant_id)
        return ControlPlaneSnapshot(
            tenant_id=tenant_id,
            environments=tuple(value for (tenant, _), value in self._environments.items() if tenant == tenant_id),
            projects=tuple(value for (tenant, _), value in self._projects.items() if tenant == tenant_id),
            resources=tuple(value for (tenant, _), value in self._resources.items() if tenant == tenant_id),
        )
