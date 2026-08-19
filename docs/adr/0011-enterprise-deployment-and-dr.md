# ADR-0011: Enterprise Deployment and Disaster Recovery

- **Status:** Accepted
- **Date:** 2026-08-19
- **Decision:** Make deployment topology, data residency, backup verification, failover, and supply-chain controls explicit platform contracts.

## Context

FDE Mastery now has stable identity, authorization, runtime, workflow, tool, model, event, evaluation, and observability boundaries. Enterprise operation requires those boundaries to survive infrastructure failure without weakening tenant isolation or security controls.

## Decision

1. Support regional and dedicated deployment profiles without changing application contracts.
2. Treat tenant data residency as an explicit deployment policy, not an implicit infrastructure property.
3. Define RPO/RTO targets per service tier and test them through repeatable recovery procedures.
4. Require encrypted backups, retention controls, restore verification, and evidence capture.
5. Treat failover as a controlled operation with fencing, dependency health checks, and post-failover reconciliation.
6. Require immutable release provenance, SBOM evidence, dependency auditing, and signed/attested artifacts before production promotion.
7. Keep secrets outside source control and require rotation procedures for recovery operations.
8. Preserve the existing fail-closed identity, tenant, policy, tool, model, event, and cost controls during degraded-mode operation.

## Consequences

The platform gains a provider-neutral enterprise deployment contract and a concrete DR runbook. Cloud-specific Terraform remains an adapter concern; the platform core does not depend on a single cloud provider. Recovery evidence becomes an operational artifact rather than an undocumented assumption.

## Rejected alternatives

- **Single-region only:** insufficient for enterprise availability and regional resilience.
- **Provider-specific core abstractions:** creates lock-in and makes testing recovery topology harder.
- **Backup-only DR:** backups without restore verification do not establish recoverability.
- **Active-active everywhere:** adds substantial consistency and operational complexity before workload requirements justify it.
