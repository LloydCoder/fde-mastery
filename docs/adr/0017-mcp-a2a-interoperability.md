# ADR-0017 — MCP / A2A Interoperability

## Status

Accepted — Build 16.

## Context

FDE MASTERY needs to consume and expose interoperable agent/tool capabilities without allowing protocol adapters to become alternate authorization or execution systems. MCP and A2A are evolving standards and both emphasize authenticated transport, explicit capability discovery and server-side authorization.

## Decision

Implement MCP and A2A as protocol boundaries over existing platform trust planes.

MCP requests are tenant-bound and authorization-bound. Header/body routing metadata is validated before protected operations. Tool catalogs are tenant-scoped and scopes are checked before a tool can be considered eligible. Actual execution continues through the existing Tool Gateway.

A2A uses Agent Cards for discovery, explicit skills and security schemes, HTTPS endpoint validation, tenant-scoped agent registration and explicit authorization before task execution. Long-running A2A tasks map to existing durable workflow IDs instead of introducing another task runtime.

Protocol revisions are explicit. The platform does not advertise wire-level conformance solely from type compatibility; transport conformance requires dedicated protocol adapter tests.

## Consequences

Positive:

- External MCP/A2A ecosystems can connect through stable platform contracts.
- Identity, authorization, approvals and execution remain centralized.
- Tenant boundaries are enforced at discovery and execution boundaries.
- Long-running agent work has one durable runtime.
- Protocol evolution can be isolated behind versioned adapters.

Trade-offs:

- Full wire-level conformance still requires transport adapters and conformance fixtures.
- Agent Card and MCP discovery data require operational cache/invalidation policy when exposed over HTTP.
- Protocol-specific extensions should remain opt-in until conformance tests exist.

## Research references

- MCP Specification 2026-07-28.
- A2A Protocol Specification 1.0.0.
- OAuth 2.0 Security Best Current Practice and the project's existing authorization plane.
