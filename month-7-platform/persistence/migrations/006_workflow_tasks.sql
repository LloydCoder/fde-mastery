-- Build 4: durable leased task queue.
-- Claims use row-level locking with SKIP LOCKED so multiple workers can safely
-- consume the same tenant-scoped queue without duplicate claims.

CREATE TABLE IF NOT EXISTS fde_workflow_tasks (
    task_id VARCHAR(36) PRIMARY KEY,
    workflow_run_id VARCHAR(36) NOT NULL REFERENCES fde_workflow_runs(workflow_run_id) ON DELETE CASCADE,
    tenant_id VARCHAR(63) NOT NULL REFERENCES fde_tenants(tenant_id) ON DELETE CASCADE,
    step_id VARCHAR(128) NOT NULL,
    attempt INTEGER NOT NULL CHECK (attempt >= 1),
    idempotency_key VARCHAR(512) NOT NULL UNIQUE,
    available_at TIMESTAMPTZ NOT NULL,
    lease_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fde_workflow_tasks_claim
    ON fde_workflow_tasks(tenant_id, available_at, lease_until);

ALTER TABLE fde_workflow_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE fde_workflow_tasks FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS fde_workflow_tasks_tenant_isolation ON fde_workflow_tasks;
CREATE POLICY fde_workflow_tasks_tenant_isolation
    ON fde_workflow_tasks
    AS RESTRICTIVE
    FOR ALL
    USING (tenant_id = fde_current_tenant_id())
    WITH CHECK (tenant_id = fde_current_tenant_id());
