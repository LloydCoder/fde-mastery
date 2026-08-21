# Build 15 — Enterprise Integration Plane

## Objective

Provide a provider-neutral, tenant-scoped integration control plane for enterprise SaaS/API systems while keeping all external side effects behind the existing Tool Gateway.

## Delivered

- Tenant + environment scoped integration bindings.
- Provider/version/capability metadata and explicit lifecycle status.
- Opaque managed credential references; credential material is rejected from contracts.
- OAuth 2.0 authorization-code + PKCE request primitives using S256, state and HTTPS endpoints.
- Authenticated webhook verification using HMAC-SHA256 and constant-time comparison.
- Timestamped webhook verification and replay protection.
- Persistent tenant-isolated integration metadata and webhook delivery idempotency ledger.
- SSRF-aware HTTPS outbound endpoint policy with explicit host allowlisting and private/reserved network rejection by default.
- Redirects disabled at the outbound integration boundary to prevent allowlist bypasses.
- Bounded retry classification with Retry-After support and exponential jitter.
- In-memory token-bucket reference limiter for connector-level throttling.
- Integration actions bridge into the existing Tool Gateway for authorization, capability checks, approval and idempotency; no second executor was introduced.
- Existing generic custom webhook was hardened from mock/fail-open behavior to explicit HTTPS allowlisting and fail-closed configuration.
- Security/contract tests covering tenant isolation, credential handling, OAuth PKCE, webhook signatures/replay, SSRF controls and retry/rate-limit behavior.

## Architecture

```text
Customer / Tenant
       │
       ▼
Integration Binding
       │
       ├── provider + version
       ├── capabilities
       ├── credential_ref ─────► Managed Secrets Provider
       ├── endpoint allowlist
       └── lifecycle status
       │
       ├───────────────┐
       ▼               ▼
 OAuth / Webhooks   Outbound HTTP Policy
       │               │
       ▼               ▼
   Integration Adapter
           │
           ▼
   Existing Tool Gateway
           │
     Policy / Approval /
     Capability / Idempotency
           │
           ▼
      External System
```

## Security model

- Integration metadata is tenant/environment scoped.
- Credential values never belong in integration contracts or source control.
- Production secret access remains delegated to managed secret backends.
- OAuth uses authorization-code + PKCE/S256 and state.
- Webhooks require cryptographic verification and delivery-id replay protection.
- Outbound integration endpoints require HTTPS and explicit host allowlisting.
- Private, loopback, link-local, reserved, multicast and common cloud metadata targets are blocked by default.
- Redirect following is disabled at the secure outbound boundary.
- Integration actions do not bypass the Tool Gateway; high-impact actions remain approval-gated.
- Retry behavior is bounded and respects server-provided Retry-After where present.

## Research basis

The design follows current OAuth security guidance, webhook signature/replay guidance, OWASP SSRF and secrets-management guidance, and OWASP agentic application security guidance. GitHub's webhook documentation specifically recommends HMAC-SHA256 verification and unique delivery IDs for replay protection. OWASP recommends treating external API responses as untrusted and keeping credentials outside agent context/logs. OAuth security best practice favors authorization-code + PKCE and state protection. 

References:

- IETF OAuth 2.0 Security Best Current Practice (RFC 9700).
- GitHub webhook signature validation and webhook best practices.
- OWASP SSRF Prevention Cheat Sheet.
- OWASP Secrets Management Cheat Sheet.
- OWASP Securing Agentic Applications Guide.

## Verification

Build 15 is complete only after the complete Platform Quality workflow is green, including pytest, domain checks, enterprise controls, migration validation, Ruff, MyPy, Bandit, dependency audit, compile validation, Terraform, SBOM, staging/load smoke, production Docker runtime smoke and Semgrep.

## Version

Platform version: **1.14.0**
