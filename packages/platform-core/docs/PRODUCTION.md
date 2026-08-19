# Production deployment reference

This reference defines the minimum production topology for the Month 7 platform.

```text
Internet
  |
  v
TLS ingress / API gateway
  |
  v
FastAPI replicas -----> Redis (managed, TLS)
  |
  +--------------------> PostgreSQL (managed, TLS)
  |
  +--------------------> OpenTelemetry Collector
                             |
                             +--> traces/metrics backend
```

## Required production settings

```text
FDE_ENVIRONMENT=production
FDE_STORAGE_BACKEND=postgres
FDE_RATE_LIMIT_BACKEND=redis
FDE_DATABASE_URL=<managed-postgresql-tls-url>
FDE_REDIS_URL=<managed-redis-tls-url>
FDE_OIDC_ISSUER=https://<identity-provider>
FDE_OIDC_AUDIENCE=<audience>
OTEL_ENABLED=true
```

Use a secret manager for credentials. Do not place secrets in `.env` files committed to Git.

## Deployment order

1. Provision managed PostgreSQL and Redis with TLS and private/network controls.
2. Apply `python -m persistence.migrate` before starting application replicas.
3. Deploy the immutable GHCR image produced by the release workflow.
4. Verify `/health` and `/ready` (or the deployment's configured health endpoints).
5. Verify OIDC authentication and tenant/scope authorization.
6. Verify telemetry reaches the configured OpenTelemetry Collector.
7. Run the smoke suite against the staging environment.

## Rollback

Deploy the previous immutable image digest. Never roll back by rebuilding `main`.

Database migrations must be backward-compatible with the application version being rolled back to. Destructive schema changes require a separate expand/migrate/contract release plan.

## Operational controls

- managed database backups and point-in-time recovery
- Redis high availability appropriate to workload
- least-privilege database credentials
- TLS for database/Redis/telemetry connections
- centralized logs and alerting
- image signature verification before deployment
- SBOM/provenance retention
- incident-response and key-rotation procedures
