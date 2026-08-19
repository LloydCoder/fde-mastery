# FDE Platform — Remaining Roadmap

This roadmap is ordered by production risk and engineering value. A roadmap item is not considered complete until implementation, tests, documentation, and CI evidence exist.

## P0 — Production safety

- [ ] Integrate resilience executor into every domain adapter with explicit per-domain policy.
- [ ] Add standardized error responses and failure audit events at the API boundary.
- [ ] Add timeout/retry/circuit/concurrency metrics and dashboards.
- [ ] Add idempotency keys for state-changing requests and retry-safe execution semantics.
- [ ] Add graceful shutdown/draining for in-flight agent requests.
- [ ] Add request deadlines propagated from gateway to adapter/provider.
- [ ] Add PostgreSQL transaction boundaries and rollback tests for usage + audit writes.
- [ ] Add Redis failure-mode tests and fail-open/fail-closed policy documentation.

## P0 — Security

- [ ] Complete an OWASP ASVS 5.0 verification matrix for the API. ASVS 5.0.0 is the current stable standard. urlOWASP ASVS 5.0https://owasp.org/www-project-application-security-verification-standard/
- [ ] Add security regression tests for authorization, tenant isolation, injection, CORS, headers, request limits, and error leakage.
- [ ] Add secret scanning and dependency/license policy to CI.
- [ ] Add SBOM generation and container image vulnerability scanning.
- [ ] Pin GitHub Actions by immutable SHA for supply-chain hardening.
- [ ] Add least-privilege deployment and database roles.
- [ ] Add production secret-rotation procedure.
- [ ] Add AI-specific controls for prompt injection, tool abuse, data exfiltration, and excessive agency.

## P1 — Reliability and scale

- [ ] Add background job execution for long-running agent tasks.
- [ ] Add durable job status and cancellation.
- [ ] Add distributed tracing with OpenTelemetry.
- [ ] Add structured JSON logs and correlation across API, workers, database, and Redis.
- [ ] Add SLOs/SLIs for availability, latency, error rate, and agent success rate.
- [ ] Add load tests and concurrency benchmarks.
- [ ] Add database connection-pool sizing and failure tests.
- [ ] Add Redis reconnect/backoff and outage recovery tests.
- [ ] Add horizontal scaling deployment manifests.

## P1 — Data and governance

- [ ] Add audit-event retention and archival policy.
- [ ] Add audit-event integrity controls and restricted administrative access.
- [ ] Add tenant data export/deletion workflows.
- [ ] Add data classification and sensitive-field redaction.
- [ ] Add configurable PII/secret redaction in logs and audit metadata.
- [ ] Add backup/restore tests and disaster-recovery runbook.

## P1 — AI platform quality

- [ ] Add domain-specific evaluation datasets for all six agents.
- [ ] Add regression evaluation gates to CI.
- [ ] Add hallucination/grounding evaluation where domain data is available.
- [ ] Add prompt/version tracking.
- [ ] Add model/provider abstraction and fallback strategy.
- [ ] Add cost/token accounting per tenant and domain.
- [ ] Add model latency and quality metrics.
- [ ] Add adversarial AI security evaluation.

## P2 — Developer experience

- [ ] Add OpenAPI examples for every public endpoint.
- [ ] Add local Docker Compose for API + PostgreSQL + Redis.
- [ ] Add one-command bootstrap and test commands.
- [ ] Add pre-commit hooks.
- [ ] Add architecture decision records for major platform decisions.
- [ ] Add contribution and release guides.
- [ ] Add changelog and semantic versioning policy.

## P2 — Delivery

- [ ] Add staging deployment workflow.
- [ ] Add production deployment workflow with protected GitHub environment.
- [ ] Add deployment smoke tests.
- [ ] Add rollback workflow.
- [ ] Add migration safety checks before deployment.
- [ ] Add release artifacts and provenance/attestation.

## Portfolio evidence

For every completed item, retain a concise evidence trail: implementation commit, tests, CI result, security rationale, and documentation. This makes the repository demonstrate FDE execution rather than merely list technologies.
