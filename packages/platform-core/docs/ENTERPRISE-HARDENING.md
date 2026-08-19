# Enterprise Production Hardening

This document is the implementation contract for the platform's production controls.

## Identity and authorization

- OIDC discovery + rotating JWKS validation.
- Required `iss`, `aud`, `sub`, `iat`, and `exp` claims.
- Tenant claim enforcement at the API boundary.
- Scope-based authorization for domain actions.
- Short-lived service tokens for environments without a service mesh.
- mTLS identity validation is supported when TLS is terminated by the mesh/ingress layer.
- Authentication decisions must include subject, tenant, action, outcome and request ID in structured audit logs.

## Secrets

Production defaults to `FDE_SECRETS_BACKEND=managed` and fails closed until a managed provider is injected. Local/test environments may use the explicit `environment` provider. Long-lived provider credentials must never be committed, baked into images, or written to audit logs.

## AI security

The request boundary applies deterministic redaction and a policy gate before domain execution. High-impact actions can require human approval based on action, severity, confidence, amount and client tier. The red-team corpus runs in CI and continuous evaluation.

## Mutation safety

Mutation endpoints accept `X-Idempotency-Key`. Production triage requires it. Reusing a key with a different request fingerprint returns `409 Conflict`. The PostgreSQL migration provides a durable idempotency table for replacing the test-memory implementation with a distributed store.

## Audit integrity

Audit events are persisted centrally. The hash-chain utility provides tamper-evident chaining; production deployments should persist the chain head and replicate immutable audit records to a separate retention-controlled store.

## Data protection

PostgreSQL and Redis production references require encryption at rest and in transit. Retention and deletion must be implemented at the tenant policy layer before regulated production data is enabled.

## Reliability

Each domain has an isolated resilience executor with timeout, bounded retries, jitter, circuit breaking and concurrency limits. Chaos tests verify failure isolation. Long-running actions should use the queue boundary documented in `DEPLOYMENT.md` rather than holding an HTTP request open.

## Observability

OpenTelemetry is the tracing contract. Export through an OTLP Collector in production. Metrics include request rate, latency, errors, rate-limit events, usage and evaluation signals. Correlation is carried through `X-Request-ID` and trace context.

## Supply chain

Releases generate a CycloneDX SBOM and use keyless signing/attestation. Production admission should verify image signatures and provenance before deployment.

## Infrastructure

Terraform provisions private PostgreSQL and Redis with encryption, automatic failover, backups and deletion protection. The application tier must run in private networking behind a TLS-terminating load balancer/WAF, with restricted administrative access and controlled LLM egress.

## Recovery targets

Production teams must define explicit RPO/RTO per tenant tier, test restore procedures, and use immutable image digests for rollback. A failed canary must prevent promotion.
