"""Small, deterministic migration runner for the platform schema.

For the portfolio deployment, migrations are tracked in PostgreSQL itself so
schema changes are explicit and repeatable. This is intentionally narrow; a
larger production organization may replace it with Alembic without changing
the repository contract.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine, text

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _migration_files() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"))


def migrate(database_url: str | None = None) -> list[str]:
    url = database_url or os.getenv("FDE_DATABASE_URL")
    if not url:
        raise ValueError("FDE_DATABASE_URL is required")

    engine = create_engine(url, pool_pre_ping=True)
    applied: list[str] = []
    with engine.begin() as connection:
        connection.execute(text(
            """
            CREATE TABLE IF NOT EXISTS fde_schema_migrations (
                version VARCHAR(100) PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))
        existing = {
            row[0]
            for row in connection.execute(text("SELECT version FROM fde_schema_migrations"))
        }

        for migration in _migration_files():
            version = migration.name
            if version in existing:
                continue
            sql = migration.read_text(encoding="utf-8")
            for statement in (part.strip() for part in sql.split(";")):
                if statement:
                    connection.execute(text(statement))
            connection.execute(
                text("INSERT INTO fde_schema_migrations (version) VALUES (:version)"),
                {"version": version},
            )
            applied.append(version)
    return applied


if __name__ == "__main__":
    applied = migrate()
    print("Applied migrations:" if applied else "No pending migrations.")
    for version in applied:
        print(f"- {version}")
