# Platform Persistence

Month 7 separates application logic from storage through `PlatformRepository`.

## Backends

- `InMemoryPlatformRepository` — deterministic local/test backend.
- `PostgreSQLPlatformRepository` — durable backend for deployed environments.

## Environment

```bash
FDE_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/fde_mastery
```

Required packages:

```bash
pip install sqlalchemy psycopg[binary]
```

## Schema

The initial SQL schema is in:

`migrations/001_initial.sql`

For production, use a migration runner and a tracked migration history rather than calling `Base.metadata.create_all()` on application startup.

## Security

Never place database credentials in source control. Use environment variables or a managed secret store. Use TLS for remote PostgreSQL connections and a least-privileged database role.
