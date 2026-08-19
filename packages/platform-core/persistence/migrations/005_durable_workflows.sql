-- Build 4: durable workflow state and append-only history.
--
-- Workflow runs and history are tenant-owned. RLS is intentionally FORCE-enabled
-- so table ownership cannot accidentally bypass tenant isolation. Workflow history
-- is immutable at the database boundary as well as in the application contract.

CREATE TABLE IF NOT EXISTS fde_workflow_runs (
    workflow_run_id VARCHAR(36) PRIMARY KEY,
    workflow_instance_id VARCHAR(128) NOT NULL UNIQUE,
    request_id VARCHAR(128) NOT NULL,
    tenant_id VARCHAR(63) NOT NULL REFERENCES fde_tenants(tenant_id) ON DELETE CASCADE,
    environment VARCHAR(32) NOT NULL
        CHECK (environment IN ('development', 'staging', 'production')),
    workflow_id VARCHAR(128) NOT NULL,
    workflow_version VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL
        CHECK (status IN ('created', 'running', 'waiting', 'completed', 'failed', 'cancelled', 'timed_out', 'dead_lettered')),
    current_step INTEGER NOT NULL DEFAULT 0 CHECK (current_step >= 0),
    step_attempt INTEGER NOT NULL DEFAULT 0 CHECK (step_attempt >= 0),
    input_json TEXT NOT NULL DEFAULT '{}',
    state_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT,
    error_type VARCHAR(128),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    UNIQUE (workflow_run_id, tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_fde_workflow_runs_tenant_status
    ON fde_workflow_runs(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_fde_workflow_runs_request
    ON fde_workflow_runs(tenant_id, request_id);

CREATE TABLE IF NOT EXISTS fde_workflow_events (
    event_id VARCHAR(36) PRIMARY KEY,
    workflow_run_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(63) NOT NULL,
    sequence INTEGER NOT NULL CHECK (sequence >= 0),
    event_type VARCHAR(128) NOT NULL,
    step_id VARCHAR(128),
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workflow_run_id, sequence),
    CONSTRAINT fk_fde_workflow_events_run_tenant
        FOREIGN KEY (workflow_run_id, tenant_id)
        REFERENCES fde_workflow_runs(workflow_run_id, tenant_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fde_workflow_events_run_sequence
    ON fde_workflow_events(workflow_run_id, sequence);

ALTER TABLE fde_workflow_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE fde_workflow_runs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS fde_workflow_runs_tenant_isolation ON fde_workflow_runs;
CREATE POLICY fde_workflow_runs_tenant_isolation
    ON fde_workflow_runs
    AS RESTRICTIVE
    FOR ALL
    USING (tenant_id = fde_current_tenant_id())
    WITH CHECK (tenant_id = fde_current_tenant_id());

ALTER TABLE fde_workflow_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE fde_workflow_events FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS fde_workflow_events_tenant_isolation ON fde_workflow_events;
CREATE POLICY fde_workflow_events_tenant_isolation
    ON fde_workflow_events
    AS RESTRICTIVE
    FOR ALL
    USING (tenant_id = fde_current_tenant_id())
    WITH CHECK (tenant_id = fde_current_tenant_id());

CREATE OR REPLACE FUNCTION fde_prevent_workflow_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'fde_workflow_events is append-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_fde_workflow_events_immutable ON fde_workflow_events;
CREATE TRIGGER trg_fde_workflow_events_immutable
BEFORE UPDATE OR DELETE ON fde_workflow_events
FOR EACH ROW
EXECUTE FUNCTION fde_prevent_workflow_event_mutation();

COMMENT ON TABLE fde_workflow_events IS
    'Append-only durable workflow history. Consumers reconstruct execution state from ordered facts.';
