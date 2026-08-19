# Build 11 — Enterprise Deployment & Disaster Recovery

## Objective

Make FDE Mastery operable as an enterprise platform across regional, dedicated, and disaster-recovery deployment profiles without coupling the platform kernel to one cloud provider.

## Capability matrix

| Capability | Contract | Enterprise requirement |
|---|---|---|
| Deployment profiles | Regional / dedicated | Explicit topology and data-residency policy |
| Availability | Health + dependency gates | No promotion when critical dependencies are unhealthy |
| Backups | Encrypted snapshots + WAL/CDC where supported | Restore verification required |
| Recovery | RPO/RTO policy | Tested recovery procedure and evidence |
| Failover | Fencing + promotion | Prevent split-brain and duplicate writers |
| Data residency | Tenant deployment policy | Residency checked before provisioning and migration |
| Supply chain | SBOM + dependency audit + attestation | Release provenance required for production |
| Secrets | External secret manager | No plaintext recovery credentials in Git |
| Operations | Runbooks + evidence | Recovery events are auditable |

## Deployment profiles

### Regional

A tenant is assigned to a primary region and an approved recovery region. Data-bearing services remain within the allowed residency set. Cross-region telemetry is minimized and must not bypass residency policy.

### Dedicated

A tenant receives an isolated deployment boundary and dedicated data plane. Shared control-plane services may remain provider-neutral where contractually permitted, but tenant data-plane traffic is explicitly scoped.

### Recovery

Recovery uses a declared recovery point, fenced writers, verified dependencies, schema compatibility checks, and reconciliation before traffic is restored.

## Recommended service tiers

| Tier | Example workload | Target RPO | Target RTO |
|---|---|---:|---:|
| Standard | Internal FDE workloads | 1 hour | 4 hours |
| Business | Customer production | 15 minutes | 1 hour |
| Critical | Mission-critical automation | 5 minutes | 30 minutes |

Targets are policy defaults. A customer contract may tighten them; it must not silently weaken tenant-isolation or security requirements.

## Recovery procedure

1. Declare incident and freeze non-essential changes.
2. Identify the last known-good recovery point.
3. Fence the failed primary to prevent split-brain writes.
4. Verify recovery-region identity, policy, secret, network, database, queue, and model/tool dependencies.
5. Restore database state and apply only validated migrations.
6. Verify tenant/RLS controls and workflow/event idempotency invariants.
7. Restore outbox/inbox processing with duplicate-safe consumers.
8. Verify model/tool policy gates before enabling external side effects.
9. Run smoke, security, and data-integrity checks.
10. Promote the recovery region and shift traffic.
11. Reconcile events, workflow states, cost ledger entries, and audit records.
12. Record RPO/RTO evidence, exceptions, and follow-up actions.

## Backup requirements

- Encryption at rest and in transit.
- Separate backup credentials from application credentials.
- Retention aligned with contractual and regulatory requirements.
- At least one recovery copy protected from accidental deletion or ransomware-style destructive access.
- Scheduled restore verification.
- Evidence includes backup timestamp, restore point, duration, checksum/integrity result, schema version, and validation result.

## Supply-chain requirements

Production artifacts must have reproducible build metadata where practical, dependency audit results, an SBOM, source revision provenance, and release attestation. Untrusted artifacts are not promoted solely because they passed application tests.

## Failure-domain rules

The platform remains a modular monolith until operational evidence justifies service extraction. Recovery boundaries follow actual stateful dependencies: PostgreSQL, queues/event persistence, object storage, secrets, external providers, and observability backends.

## Security invariants during recovery

- Identity remains fail closed.
- Tenant context is mandatory.
- PostgreSQL RLS remains enforced.
- Policy decisions remain fail closed.
- Tool and model approvals are not bypassed.
- External side effects remain idempotent.
- Sensitive telemetry remains subject to the same privacy controls.

## Verification

Build 11 is complete only when the repository quality workflow is green and the deployment/DR contract tests validate the machine-readable recovery policy.
