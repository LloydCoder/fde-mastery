# Configuration reference

FDE Mastery configuration is environment-driven. The tracked API gateway example is [packages/platform-core/deployment/api_gateway/.env.example](../packages/platform-core/deployment/api_gateway/.env.example). It contains placeholders and local-development examples only.

## API gateway variables

| Variable | Example in template | Purpose |
|---|---|---|
| `FDE_API_KEYS` | Placeholder | Comma-separated application API keys |
| `FDE_ADMIN_API_KEYS` | Placeholder | Separate administrator API keys; do not reuse application keys |
| `FDE_STORAGE_BACKEND` | `memory` | Selects in-memory or PostgreSQL storage |
| `FDE_DATABASE_URL` | Local PostgreSQL DSN | PostgreSQL connection when durable storage is selected |
| `FDE_DB_CREATE_TABLES` | `false` | Controls automatic table creation |
| `FDE_RATE_LIMIT_BACKEND` | `memory` | Selects process-local or Redis-backed rate limiting |
| `FDE_REDIS_URL` | Local Redis URL | Redis connection when Redis rate limiting is selected |
| `FDE_RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window in seconds |
| `FDE_RATE_LIMIT_REQUESTS` | `60` | Request allowance per configured window |
| `FDE_MAX_BODY_BYTES` | `262144` | Maximum accepted request body size |

## Local test profile

The repository test workflow uses mock/in-memory settings:

```bash
FDE_STORAGE_BACKEND=memory
FDE_RATE_LIMIT_BACKEND=memory
FDE_MONTH1_PROVIDER=mock
MOCK_LLM=true
FDE_ENVIRONMENT=test
```

These settings are for local tests. In-memory storage and process-local rate limiting are not appropriate for horizontally scaled production deployments.

## Production profile

The production Compose definition is [packages/platform-core/deployment/docker-compose.production.yml](../packages/platform-core/deployment/docker-compose.production.yml). It selects PostgreSQL, Redis and managed secrets and expects deployment-provided values for:

- `POSTGRES_PASSWORD`
- `FDE_OIDC_ISSUER`
- `FDE_OIDC_AUDIENCE`
- `FDE_OIDC_JWKS_URL` (optional in Compose interpolation)
- `FDE_OIDC_ALGORITHMS` (defaults to `RS256` in the Compose file)
- `FDE_API_KEYS`
- `FDE_ADMIN_API_KEYS`
- OTLP endpoints and service name when telemetry export is enabled

Use a secret manager or protected deployment environment for production credentials. Do not commit populated environment files, private keys, database dumps or customer configuration.

## Configuration safety

- Use separate application and administrator credentials.
- Rotate credentials after suspected exposure.
- Restrict database and Redis network access.
- Configure OIDC issuer and audience for the intended identity provider.
- Keep TLS termination and trusted proxy configuration consistent with the deployment environment.
- Review retention, data classification and audit requirements for each customer.
- Verify actual deployment configuration before declaring a customer environment production-ready.

This reference documents variables confirmed in the checked-in example and production Compose file. Other optional provider settings are owned by their integration modules; inspect module implementation before relying on undocumented variables.
