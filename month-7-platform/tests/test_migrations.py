from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from persistence.migrations import MigrationError, run_migrations


def test_migrations_are_versioned_and_idempotent(tmp_path: Path):
    (tmp_path / "0001_first.sql").write_text("CREATE TABLE example_one (id INTEGER);", encoding="utf-8")
    (tmp_path / "0002_second.sql").write_text("CREATE TABLE example_two (id INTEGER);", encoding="utf-8")
    engine = create_engine("sqlite://")
    with engine.connect() as connection:
        assert run_migrations(connection, tmp_path) == [1, 2]
        assert run_migrations(connection, tmp_path) == []
        assert connection.execute(text("SELECT COUNT(*) FROM fde_schema_migrations")).scalar_one() == 2


def test_changed_applied_migration_is_rejected(tmp_path: Path):
    path = tmp_path / "0001_first.sql"
    path.write_text("CREATE TABLE example_one (id INTEGER);", encoding="utf-8")
    engine = create_engine("sqlite://")
    with engine.connect() as connection:
        run_migrations(connection, tmp_path)
        path.write_text("CREATE TABLE example_changed (id INTEGER);", encoding="utf-8")
        with pytest.raises(MigrationError, match="checksum changed"):
            run_migrations(connection, tmp_path)
