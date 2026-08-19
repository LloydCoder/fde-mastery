# Production Deployment

## Required services

- PostgreSQL for durable state
- Redis for distributed rate limiting
- OIDC provider for enterprise identity
- OpenTelemetry Collector for telemetry

Production configuration must use `FDE_ENVIRONMENT=production`, `FDE_STORAGE_BACKEND=postgres`, `FDE_RATE_LIMIT_BACKEND=redis`, and `MOCK_LLM=false`.

## Deployment gates

1. Run the complete CI workflow.
2. Review the generated CycloneDX SBOM.
3. Run database migrations before application rollout.
4. Deploy the new image with a readiness probe.
5. Verify `/health` and `/ready`.
6. Run one synthetic request for each of the six domains.
7. Monitor error rate, latency, circuit-open events and dependency failures.

## Rollback

Keep the previous immutable image available. If health, error rate or synthetic checks fail, stop promotion and redeploy the previous image. Never roll back application code while silently changing the database schema in an incompatible direction; use expand/contract migrations.

## Secrets

Store OIDC, database, Redis and model-provider credentials in the deployment secret manager. Never put credentials in Git, images, SBOMs or logs.
