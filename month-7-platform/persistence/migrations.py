"""Minimal, explicit PostgreSQL migration runner with durable version tracking."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from sqlalchemy import Connection, text

_MIGRATION = re.compile(r"^(?P<version>\d{4})_(?P<name>[a-z0-9_]+)\.sql$")


class MigrationError(RuntimeError):
    pass


def _files(directory: Path) -> list[tuple[int, Path]]:
    found: list[tuple[int, Path]] = []
    for path in directory.glob("*.sql"):
        match = _MIGRATION.match(path.name)
        if match:
            found.append((int(match.group("version")), path))
    return sorted(found)


def ensure_version_table(connection: Connection) -> None:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS fde_schema_migrations (
            version INTEGER PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            checksum VARCHAR(64) NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))


def run_migrations(connection: Connection, directory: str | Path) -> list[int]:
    migration_dir = Path(directory)
    if not migration_dir.is_dir():
        raise MigrationError(f"Migration directory does not exist: {migration_dir}")
    applied: list[int] = []
    with connection.begin():
        ensure_version_table(connection)
        rows = connection.execute(text("SELECT version, checksum FROM fde_schema_migrations")).mappings()
        existing = {int(row["version"]): str(row["checksum"]) for row in rows}
        for version, path in _files(migration_dir):
            sql = path.read_text(encoding="utf-8")
            import hashlib
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
            if version in existing:
                if existing[version] != checksum:
                    raise MigrationError(f"Migration checksum changed: {path.name}")
                continue
            connection.exec_driver_sql(sql)
            connection.execute(
                text("INSERT INTO fde_schema_migrations(version, name, checksum) VALUES (:version, :name, :checksum)"),
                {"version": version, "name": path.stem, "checksum": checksum},
            )
            applied.append(version)
    return applied


def migration_status(connection: Connection) -> list[dict[str, object]]:
    ensure_version_table(connection)
    return [dict(row) for row in connection.execute(text(
        "SELECT version, name, checksum, applied_at FROM fde_schema_migrations ORDER BY version"
    )).mappings()]
