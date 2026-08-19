"""Select the platform persistence backend from environment configuration."""

import os

from .repository import InMemoryPlatformRepository, PlatformRepository


def build_repository() -> PlatformRepository:
    backend = os.getenv("FDE_STORAGE_BACKEND", "memory").strip().lower()
    if backend == "memory":
        return InMemoryPlatformRepository()
    if backend == "postgres":
        from .postgres import PostgreSQLPlatformRepository

        return PostgreSQLPlatformRepository(
            database_url=os.getenv("FDE_DATABASE_URL"),
            create_tables=os.getenv("FDE_DB_CREATE_TABLES", "false").lower() == "true",
        )
    raise ValueError("FDE_STORAGE_BACKEND must be 'memory' or 'postgres'")
