# ADR-0016 — Enterprise Integration Plane

## Status

Accepted — Build 15.

## Context

FDE workflows must interact with customer systems such as SaaS APIs, SIEMs, CRMs, ERP/finance systems, EHRs, logistics platforms and custom webhooks. The repository already has a Tool Gateway, identity, authorization, approvals, events, persistence and observability. Creating another executor would duplicate trust boundaries and make authorization inconsistent.

## Decision

Introduce an integration control plane that owns connector metadata, tenant/environment binding, credential references, endpoint policy, OAuth/webhook protocol concerns, retry/rate-limit policy and integration lifecycle. External side effects continue through the existing Tool Gateway.

Credential material is never stored in integration contracts. Bindings hold opaque references to managed secret backends.

Inbound webhooks require signature verification and replay/idempotency controls before payload processing. Outbound endpoints require HTTPS and explicit host allowlisting; private/reserved targets are rejected by default and redirects are disabled.

## Consequences

Positive:

- One authoritative execution boundary remains in the Tool Gateway.
- Integrations become tenant/environment scoped and auditable.
- OAuth, webhook and endpoint security become reusable platform capabilities.
- Connector failures can use bounded retry/rate-limit semantics.
- Persistence has a durable integration and webhook-delivery ledger.

Trade-offs:

- Providers still require concrete adapters outside the framework-neutral contracts.
- A production deployment needs a real managed secrets backend.
- Host allowlists must be maintained as provider endpoints evolve.

## Security references

The design aligns with OAuth 2.0 Security Best Current Practice, GitHub's webhook signature/replay guidance, OWASP SSRF prevention, OWASP Secrets Management and OWASP agentic application security guidance.
