# Customer-style case study

> This is a synthetic case study for portfolio demonstration. It is not a claim of a production customer deployment.

## Scenario

A regulated fintech receives a high-volume stream of transaction-risk alerts and needs consistent triage, tenant isolation, auditability, and controlled human escalation.

## Before

- manual alert triage
- inconsistent escalation criteria
- limited request-level traceability
- no shared execution contract across AI workflows

## Platform approach

- typed domain-agent contract
- centralized router with per-domain resilience
- OIDC identity and scope/tenant authorization
- PostgreSQL persistence and audit events
- Redis-compatible distributed rate limiting
- OpenTelemetry traces/metrics
- deterministic security and red-team regression tests

## Outcome to measure in a real deployment

A real customer engagement should report measured changes in:

- alert triage time
- analyst handling capacity
- false-positive rate
- escalation accuracy
- audit retrieval time
- platform error rate and latency

No numerical customer outcome should be claimed until it is measured in an actual deployment.
