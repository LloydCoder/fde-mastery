from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "persistence" / "migrations"


def test_workflow_migration_is_tenant_isolated_and_append_only():
    sql = (MIGRATIONS / "005_durable_workflows.sql").read_text(encoding="utf-8")
    assert "fde_workflow_runs" in sql
    assert "fde_workflow_events" in sql
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "AS RESTRICTIVE" in sql
    assert "USING (tenant_id = fde_current_tenant_id())" in sql
    assert "WITH CHECK (tenant_id = fde_current_tenant_id())" in sql
    assert "UNIQUE (workflow_run_id, sequence)" in sql


def test_workflow_task_migration_supports_leases_and_safe_claims():
    sql = (MIGRATIONS / "006_workflow_tasks.sql").read_text(encoding="utf-8")
    assert "fde_workflow_tasks" in sql
    assert "idempotency_key VARCHAR(512) NOT NULL UNIQUE" in sql
    assert "lease_until TIMESTAMPTZ" in sql
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "AS RESTRICTIVE" in sql
