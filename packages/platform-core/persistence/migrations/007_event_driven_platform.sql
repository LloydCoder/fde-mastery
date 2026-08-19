-- Build 8: event-driven backbone.
--
-- The outbox solves the database/message dual-write problem: domain state and
-- publication intent are committed atomically. Delivery is intentionally
-- at-least-once; consumers must deduplicate through the inbox table.

CREATE TABLE IF NOT EXISTS fde_outbox_events (
    event_id UUID PRIMARY KEY,
    tenant_id VARCHAR(63) NOT NULL,
    environment VARCHAR(32) NOT NULL
        CHECK (environment IN ('development', 'staging', 'production')),
    event_type VARCHAR(200) NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version >= 1),
    source VARCHAR(200) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    correlation_id UUID,
    causation_id UUID,
    trace_id VARCHAR(255),
    partition_key VARCHAR(500),
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    aggregate_type VARCHAR(200),
    aggregate_id VARCHAR(255),
    aggregate_sequence BIGINT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'published', 'failed', 'dead_lettered')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    locked_by VARCHAR(255),
    locked_at TIMESTAMPTZ,
    last_error TEXT,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_fde_outbox_pending
    ON fde_outbox_events(status, available_at, created_at)
    WHERE status IN ('pending', 'failed');
CREATE INDEX IF NOT EXISTS idx_fde_outbox_tenant
    ON fde_outbox_events(tenant_id, environment, created_at);
CREATE INDEX IF NOT EXISTS idx_fde_outbox_partition
    ON fde_outbox_events(partition_key, aggregate_sequence);

ALTER TABLE fde_outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE fde_outbox_events FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS fde_outbox_tenant_isolation ON fde_outbox_events;
CREATE POLICY fde_outbox_tenant_isolation
    ON fde_outbox_events
    AS RESTRICTIVE
    FOR ALL
    USING (tenant_id = fde_current_tenant_id())
    WITH CHECK (tenant_id = fde_current_tenant_id());

CREATE TABLE IF NOT EXISTS fde_inbox_messages (
    consumer_name VARCHAR(255) NOT NULL,
    event_id UUID NOT NULL,
    tenant_id VARCHAR(63) NOT NULL,
    environment VARCHAR(32) NOT NULL
        CHECK (environment IN ('development', 'staging', 'production')),
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL DEFAULT 'processing'
        CHECK (status IN ('processing', 'processed', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 1 CHECK (attempts >= 1),
    last_error TEXT,
    PRIMARY KEY (consumer_name, event_id)
);

CREATE INDEX IF NOT EXISTS idx_fde_inbox_tenant
    ON fde_inbox_messages(tenant_id, environment, received_at);

CREATE INDEX IF NOT EXISTS idx_fde_inbox_consumer_status
    ON fde_inbox_messages(consumer_name, status, received_at);

ALTER TABLE fde_inbox_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE fde_inbox_messages FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS fde_inbox_tenant_isolation ON fde_inbox_messages;
CREATE POLICY fde_inbox_tenant_isolation
    ON fde_inbox_messages
    AS RESTRICTIVE
    FOR ALL
    USING (tenant_id = fde_current_tenant_id())
    WITH CHECK (tenant_id = fde_current_tenant_id());

COMMENT ON TABLE fde_outbox_events IS
    'Transactional publication intents. Domain writes and outbox inserts must share a transaction.';
COMMENT ON TABLE fde_inbox_messages IS
    'Consumer-side idempotency ledger for at-least-once delivery; events may originate outside this database.';
