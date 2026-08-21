# Build 16 — MCP / A2A Agent Interoperability

## Objective

Make FDE MASTERY interoperable with external MCP tools/servers and A2A agents while preserving the platform's existing identity, authorization, Tool Gateway, durable workflow and tenant-isolation boundaries.

## Delivered

### MCP

- Supported MCP protocol revisions are explicit, including `2026-07-28` and the prior `2025-11-25` revision.
- MCP requests carry tenant identity and an authorization context.
- Authorization context records issuer, subject, scopes and an opaque authorization reference.
- `Mcp-Method` and `Mcp-Name` headers are validated against request bodies to support safe header-based routing/authorization.
- Tenant-scoped MCP tool catalog prevents cross-tenant tool discovery.
- Tool scopes are enforced before protected tool use.
- Tool annotations expose read-only, destructive, idempotent and open-world risk hints without treating annotations as authorization.
- MCP tool calls remain subject to the existing Tool Gateway for actual execution and approval.

### A2A

- A2A 1.0-style Agent Cards are represented as typed contracts.
- Agent interfaces require HTTPS in production.
- Skills have stable IDs and explicit input/output modalities.
- Security schemes and scopes are declared without embedding credentials.
- Tenant-scoped Agent Card registry prevents cross-tenant discovery.
- Agent discovery is skill-aware.
- A2A requests require sender, recipient, skill, task and authorization references.
- Server-side authorization is explicit and must run before task execution.
- Agent Card endpoint host allowlisting is supported.
- A2A task handles map to existing durable workflow IDs; no second task runtime was introduced.
- A2A task visibility is tenant-scoped.

### Integration with existing architecture

```text
External MCP Client ──► MCP Protocol Boundary ──► Platform Authorization
                                              │
                                              ▼
                                        Tool Gateway
                                              │
                                              ▼
                                      Integration Plane

External A2A Agent ──► A2A Protocol Boundary ──► Identity / Authorization
                                              │
                                              ▼
                                     Durable Workflow
                                              │
                                              ▼
                                         Tool Gateway
```

The protocol layer is intentionally not an executor. This preserves one authoritative policy/action boundary.

## Security model

- HTTPS is required for production A2A endpoints.
- Authorization references are opaque and do not carry credentials.
- MCP authorization issuer, subject and tenant are validated together.
- MCP tenant mismatch fails closed.
- MCP protected tools require declared scopes.
- MCP routing headers must match the JSON-RPC request to prevent gateway/body confusion.
- A2A discovery and tasks are tenant-scoped.
- A2A skill authorization is explicit; merely receiving an A2A task does not grant permission.
- Agent Card endpoints are allowlisted before use.
- Agent Cards do not contain credential material.
- Long-running A2A work reuses the existing durable workflow runtime.

## Research basis

Build 16 was designed against the current MCP `2026-07-28` specification and A2A `1.0.0` specification. MCP's 2026 revision introduces a stateless core, header-based routing, cacheable list results, authorization hardening and an extension model; the platform therefore validates `Mcp-Method`/`Mcp-Name` consistency and keeps protocol state outside the transport. A2A 1.0 requires Agent Cards, HTTPS for HTTP transports, per-request authentication/authorization, tenant/resource scoping and explicit skill/capability discovery.

The design also follows the project's existing fail-closed authorization and Tool Gateway architecture rather than introducing a protocol-specific bypass.

## Compatibility strategy

Protocol version handling is explicit. FDE MASTERY does not silently claim full wire-level compliance merely because contracts exist. A transport adapter must use these contracts and the protocol conformance tests before a protocol version is advertised as supported in production.

## Version

Platform version: **1.15.0**
