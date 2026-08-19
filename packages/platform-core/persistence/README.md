# Platform Persistence

Month 7 separates application logic from storage through `PlatformRepository`.

## Backends

- `InMemoryPlatformRepository` — deterministic local/test backend.
- `PostgreSQLPlatformRepository` — durable backend for deployed environments.

## Environment

```bash
FDE_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/fde_mastery
FDE_STORAGE_BACKEND=postgres
```

Required packages are included in the platform package:

```bash
pip install -e "."
```

## Migrations

The platform now tracks applied migrations in `fde_schema_migrations`.

Run:

```bash
cd month-7-platform
python -m persistence.migrate
```

The migration runner applies files from `persistence/migrations/` in filename order and records each applied migration. This makes schema changes explicit and repeatable instead of relying on application startup to call `create_all()`.

For a larger production deployment, this migration contract can later be replaced by Alembic while preserving the repository interface.

## Security

Never place database credentials in source control. Use environment variables or a managed secret store. Use TLS for remote PostgreSQL connections and a least-privileged database role.
