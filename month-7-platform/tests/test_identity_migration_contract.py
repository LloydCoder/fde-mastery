from pathlib import Path


MIGRATION = Path(__file__).parents[1] / "persistence" / "migrations" / "002_identity_multitenancy.sql"


def test_identity_migration_has_default_deny_rls_primitives() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "create table if not exists fde_tenants" in sql
    assert "create table if not exists fde_tenant_memberships" in sql
    assert "create table if not exists fde_tenant_environments" in sql
    assert "enable row level security" in sql
    assert "force row level security" in sql
    assert "as restrictive" in sql
    assert "using (tenant_id = fde_current_tenant_id())" in sql
    assert "with check (tenant_id = fde_current_tenant_id())" in sql


def test_identity_migration_does_not_use_permissive_public_tenant_policy() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert " to public " not in sql
