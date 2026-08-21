"""Enterprise MCP/A2A interoperability contracts.

Protocol adapters are transport-facing only. Authorization, tenant isolation, approvals,
credential handling and side effects remain delegated to the platform trust/tool/workflow planes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping, Sequence
from urllib.parse import urlsplit


class MCPProtocolVersion(str, Enum):
    V2025_11_25 = "2025-11-25"
    V2026_07_28 = "2026-07-28"


@dataclass(frozen=True, slots=True)
class MCPToolAnnotations:
    read_only: bool = False
    destructive: bool = False
    idempotent: bool = False
    open_world: bool = False


@dataclass(frozen=True, slots=True)
class MCPAuthorizationContext:
    tenant_id: str
    subject: str
    issuer: str
    scopes: frozenset[str] = field(default_factory=frozenset)
    authorization_reference: str = ""

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.subject.strip() or not self.issuer.startswith("https://"):
            raise ValueError("MCP authorization context requires tenant, subject and HTTPS issuer")
        if not self.authorization_reference.strip():
            raise ValueError("MCP authorization reference is required")


@dataclass(frozen=True, slots=True)
class MCPRequest:
    protocol_version: MCPProtocolVersion
    method: str
    name: str | None
    request_id: str
    tenant_id: str
    authorization: MCPAuthorizationContext
    arguments: Mapping[str, object] = field(default_factory=dict)
    idempotency_key: str | None = None
    traceparent: str | None = None
    headers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.tenant_id.strip():
            raise ValueError("MCP request id and tenant are required")
        if self.authorization.tenant_id != self.tenant_id:
            raise PermissionError("MCP authorization tenant does not match request tenant")
        if self.method == "tools/call" and not self.name:
            raise ValueError("MCP tools/call requires a tool name")
        declared_method = self.headers.get("Mcp-Method")
        declared_name = self.headers.get("Mcp-Name")
        if declared_method and declared_method != self.method:
            raise ValueError("Mcp-Method header does not match request method")
        if declared_name and declared_name != (self.name or ""):
            raise ValueError("Mcp-Name header does not match request name")


@dataclass(frozen=True, slots=True)
class MCPToolCatalogEntry:
    tenant_id: str
    tool: object
    required_scopes: frozenset[str] = field(default_factory=frozenset)
    public: bool = False


class MCPToolCatalog:
    """Tenant-scoped tool catalog. Cross-tenant lookup is impossible by construction."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], MCPToolCatalogEntry] = {}

    def register(self, entry: MCPToolCatalogEntry, *, tool_name: str) -> None:
        if not entry.tenant_id.strip() or not tool_name.strip():
            raise ValueError("tenant and tool name are required")
        key = (entry.tenant_id, tool_name)
        if key in self._entries:
            raise ValueError("tool already registered for tenant")
        self._entries[key] = entry

    def get(self, tenant_id: str, tool_name: str) -> MCPToolCatalogEntry:
        try:
            return self._entries[(tenant_id, tool_name)]
        except KeyError as exc:
            raise LookupError("MCP tool is not registered for this tenant") from exc

    def authorize(self, request: MCPRequest, *, tool_name: str) -> MCPToolCatalogEntry:
        entry = self.get(request.tenant_id, tool_name)
        if entry.public:
            return entry
        if not entry.required_scopes.issubset(request.authorization.scopes):
            raise PermissionError("MCP tool scope requirement is not satisfied")
        return entry


class MCPRequestValidator:
    SUPPORTED = frozenset(MCPProtocolVersion)

    @classmethod
    def validate(cls, request: MCPRequest) -> None:
        if request.protocol_version not in cls.SUPPORTED:
            raise ValueError("unsupported MCP protocol version")
        if request.headers.get("Mcp-Method") != request.method:
            raise ValueError("Mcp-Method header is required and must match the body")
        if request.method == "tools/call" and request.headers.get("Mcp-Name") != request.name:
            raise ValueError("Mcp-Name header is required for tools/call and must match the body")


class A2ATaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass(frozen=True, slots=True)
class AgentInterface:
    url: str
    protocol_binding: str = "JSONRPC"
    tenant: str | None = None

    def __post_init__(self) -> None:
        if not self.url.startswith("https://"):
            raise ValueError("A2A production interfaces must use HTTPS")


@dataclass(frozen=True, slots=True)
class AgentSkill:
    id: str
    name: str
    description: str
    tags: tuple[str, ...] = ()
    input_modes: tuple[str, ...] = ("text/plain",)
    output_modes: tuple[str, ...] = ("text/plain",)

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.name.strip() or not self.description.strip():
            raise ValueError("A2A skill identity and description are required")


@dataclass(frozen=True, slots=True)
class SecurityScheme:
    name: str
    scheme: str
    scopes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.scheme.strip():
            raise ValueError("A2A security scheme requires a name and scheme")


@dataclass(frozen=True, slots=True)
class AgentCard:
    name: str
    description: str
    version: str
    supported_interfaces: tuple[AgentInterface, ...]
    skills: tuple[AgentSkill, ...]
    security_schemes: tuple[SecurityScheme, ...] = ()
    provider: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.description.strip() or not self.version.strip():
            raise ValueError("A2A AgentCard identity is incomplete")
        if not self.supported_interfaces:
            raise ValueError("A2A AgentCard requires at least one supported interface")
        skill_ids = [skill.id for skill in self.skills]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("A2A skill ids must be unique")


@dataclass(frozen=True, slots=True)
class A2ARequest:
    tenant_id: str
    sender_agent: str
    recipient_agent: str
    skill_id: str
    task_id: str
    authorization_reference: str
    protocol_version: str = "1.0.0"
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        values = (self.tenant_id, self.sender_agent, self.recipient_agent, self.skill_id, self.task_id, self.authorization_reference)
        if any(not value.strip() for value in values):
            raise ValueError("A2A request identity fields are required")


@dataclass(frozen=True, slots=True)
class A2ATaskRef:
    tenant_id: str
    task_id: str
    workflow_id: str
    state: A2ATaskState


class A2AAgentRegistry:
    """Tenant-scoped Agent Card registry; public discovery never crosses tenant boundaries."""

    def __init__(self) -> None:
        self._cards: dict[tuple[str, str], AgentCard] = {}

    def register(self, tenant_id: str, card: AgentCard) -> None:
        if not tenant_id.strip():
            raise ValueError("tenant id is required")
        self._cards[(tenant_id, card.name)] = card

    def get(self, tenant_id: str, agent_name: str) -> AgentCard:
        try:
            return self._cards[(tenant_id, agent_name)]
        except KeyError as exc:
            raise LookupError("agent is not registered for this tenant") from exc

    def discover(self, tenant_id: str, skill_id: str) -> tuple[AgentCard, ...]:
        return tuple(card for (bound_tenant, _), card in self._cards.items()
                     if bound_tenant == tenant_id and any(skill.id == skill_id for skill in card.skills))


class A2ATaskBridge:
    """Maps A2A task handles to existing durable workflow IDs; no second task runtime is created."""

    def __init__(self) -> None:
        self._tasks: dict[tuple[str, str], A2ATaskRef] = {}

    def create(self, tenant_id: str, task_id: str, workflow_id: str) -> A2ATaskRef:
        key = (tenant_id, task_id)
        if key in self._tasks:
            raise ValueError("A2A task already exists")
        ref = A2ATaskRef(tenant_id, task_id, workflow_id, A2ATaskState.SUBMITTED)
        self._tasks[key] = ref
        return ref

    def get(self, tenant_id: str, task_id: str) -> A2ATaskRef:
        try:
            return self._tasks[(tenant_id, task_id)]
        except KeyError as exc:
            raise LookupError("A2A task is not visible in this tenant") from exc

    def update_state(self, tenant_id: str, task_id: str, state: A2ATaskState) -> A2ATaskRef:
        current = self.get(tenant_id, task_id)
        updated = A2ATaskRef(current.tenant_id, current.task_id, current.workflow_id, state)
        self._tasks[(tenant_id, task_id)] = updated
        return updated


def validate_agent_card_endpoint(card: AgentCard, *, allowed_hosts: Sequence[str]) -> None:
    allowed = {host.lower().rstrip(".") for host in allowed_hosts}
    for interface in card.supported_interfaces:
        hostname = (urlsplit(interface.url).hostname or "").lower().rstrip(".")
        if hostname not in allowed:
            raise PermissionError("A2A AgentCard endpoint is not allowlisted")


def authorize_a2a(request: A2ARequest, card: AgentCard, authorize: Callable[[str, str, str, str], bool]) -> None:
    if request.recipient_agent != card.name:
        raise PermissionError("A2A recipient does not match the discovered AgentCard")
    if not any(skill.id == request.skill_id for skill in card.skills):
        raise PermissionError("A2A skill is not advertised by the recipient")
    if not authorize(request.tenant_id, request.sender_agent, request.skill_id, request.authorization_reference):
        raise PermissionError("A2A authorization denied")
