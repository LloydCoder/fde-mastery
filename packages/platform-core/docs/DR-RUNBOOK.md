# Disaster Recovery Runbook

## Targets

| Tier | RPO | RTO | Strategy |
|---|---:|---:|---|
| Standard | 24h | 4h | Managed PostgreSQL backups + immutable image rollback |
| Enterprise | 1h | 1h | PITR + warm standby + automated canary rollback |
| Critical | 15m | 30m | Cross-region replica + tested failover |

## PostgreSQL failure

1. Stop writes or place the tenant in maintenance mode.
2. Identify the last known-good recovery point.
3. Restore to a new isolated instance using PITR.
4. Run the migration status/checksum validation.
5. Run health, integration, and data-integrity checks.
6. Switch the application connection through the managed secret provider.
7. Re-enable traffic gradually.
8. Record the incident and recovery point.

## Redis failure

Redis is treated as ephemeral coordination/rate-limit state. Recreate the managed cluster with TLS and automatic failover enabled, then restore rate-limit configuration. Never treat Redis as the system of record.

## Application rollback

Deploy by immutable image digest. If a canary fails error-rate, latency, security, or evaluation gates, stop promotion and redeploy the last known-good digest. Do not roll back by mutating `latest`.

## Restore testing

Run a restore drill at least quarterly and record:

- recovery point achieved
- recovery time achieved
- migration status
- audit-chain verification
- tenant isolation checks
- six-domain health
- trace/metric delivery

A backup is not considered production-ready until a restore has been successfully demonstrated.
