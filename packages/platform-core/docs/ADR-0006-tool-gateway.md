# ADR-0006: Capability-scoped Tool Gateway

## Status

Accepted — Build 6.

## Context

Agents need controlled access to external functions and systems. Direct access from an agent to arbitrary Python callables, network clients, databases, shell commands, or provider SDKs creates an excessive-agency boundary and makes authorization, auditing, idempotency, and tenant isolation difficult to enforce consistently.

## Decision

All platform-level agent tool invocation crosses a framework-neutral `ToolGateway` port.

The gateway uses:

- immutable, versioned `ToolDefinition` metadata;
- explicit capabilities (`read`, `write`, `delete`, `external_network`, `sensitive_data`);
- fail-closed registration and lookup;
- request-context binding to prevent execution outside the authenticated request;
- explicit approval requirements for high-impact tools;
- idempotency keys to make repeated delivery safe;
- a small `ToolResult` envelope instead of leaking arbitrary adapter exceptions.

Concrete integrations remain outside the kernel and can later implement MCP, HTTP, RPC, database, SaaS, or local adapters without changing agent contracts.

## Security rationale

The gateway is a policy enforcement point, not a convenience wrapper. An agent cannot expand its own capabilities, invoke an unregistered tool, bypass the request context, or execute an approval-gated tool. This follows least privilege and complete mediation principles and directly addresses OWASP GenAI risks around excessive functionality, permissions, and autonomy.

MCP integration, when added, must preserve this boundary. Transport authorization, token audience validation, short-lived credentials, and secure token handling remain required at the MCP adapter boundary; MCP is not treated as a trust boundary by itself.

## Consequences

Positive:

- one auditable tool-invocation boundary;
- safer agent extensibility;
- deterministic tests and idempotency semantics;
- clean separation between kernel contracts and provider-specific adapters;
- future MCP compatibility without coupling the core to MCP.

Trade-off:

- every tool integration needs an adapter and explicit registration;
- production gateways will need durable idempotency and audit storage rather than the in-memory reference implementation.

Those production concerns are intentionally addressed by later platform builds without weakening the Build 6 boundary.
