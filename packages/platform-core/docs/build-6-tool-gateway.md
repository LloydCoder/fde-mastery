# Build 6 — Tool Gateway

Build 6 establishes the platform's first-class tool invocation boundary.

## Architecture

```text
Agent Runtime
     |
     v
 ToolGateway (port)
     |
     +--> registration + capability check
     +--> request-context binding
     +--> approval boundary
     +--> idempotency
     |
     v
 Tool Adapter
     |
     +--> SaaS / HTTP / DB / RPC / MCP
```

## Rules

1. Tools are explicitly registered.
2. Tool definitions are immutable and versioned.
3. Capabilities are additive and explicit; the caller cannot grant itself capabilities that the registered tool does not possess.
4. Every invocation is bound to the authenticated `RequestContext` request ID.
5. High-impact tools can require approval before execution.
6. Repeated calls with the same `(tool, idempotency_key)` return the stored result in the reference gateway.
7. Unknown tools and policy violations fail closed.
8. Adapters must enforce downstream authorization themselves; the gateway does not replace downstream authorization.
9. Arbitrary shell/URL/network primitives should not be exposed when a narrower tool can satisfy the use case.

## MCP boundary

MCP is treated as an integration protocol, not an authorization bypass. An MCP adapter must map the platform principal, tenant, environment, policy decision, capability set, and audit context into the downstream request. HTTP-based MCP deployments must additionally follow the applicable OAuth authorization and token-audience requirements.
