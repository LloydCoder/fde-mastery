CREATE TABLE IF NOT EXISTS fde_audit_events (
    event_id VARCHAR(100) PRIMARY KEY,
    request_id VARCHAR(100) NOT NULL,
    client_id VARCHAR(100) NOT NULL REFERENCES fde_clients(client_id) ON DELETE CASCADE,
    domain VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    outcome VARCHAR(30) NOT NULL,
    status_code INTEGER NOT NULL CHECK (status_code BETWEEN 100 AND 599),
    duration_ms DOUBLE PRECISION NOT NULL CHECK (duration_ms >= 0),
    created_at TIMESTAMPTZ NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_fde_audit_request_id ON fde_audit_events(request_id);
CREATE INDEX IF NOT EXISTS idx_fde_audit_client_created ON fde_audit_events(client_id, created_at DESC);
