"""CLI wrapper around the canonical checksum-verified migration runner."""

from __future__ import annotations

import os

from sqlalchemy import create_engine

from .migrations.runner import MIGRATIONS_DIR, run_migrations


def migrate(database_url: str | None = None) -> list[int]:
    url = database_url or os.getenv("FDE_DATABASE_URL")
    if not url:
        raise ValueError("FDE_DATABASE_URL is required")
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as connection:
        return run_migrations(connection, MIGRATIONS_DIR)


if __name__ == "__main__":
    applied = migrate()
    print("Applied migrations:" if applied else "No pending migrations.")
    for version in applied:
        print(f"- {version}")
