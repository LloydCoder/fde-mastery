CREATE TABLE IF NOT EXISTS fde_idempotency_keys (
    client_id VARCHAR(100) NOT NULL REFERENCES fde_clients(client_id) ON DELETE CASCADE,
    idempotency_key VARCHAR(200) NOT NULL,
    request_fingerprint CHAR(64) NOT NULL,
    response_json TEXT NOT NULL,
    status_code INTEGER NOT NULL CHECK (status_code BETWEEN 100 AND 599),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (client_id, idempotency_key)
);

ALTER TABLE fde_audit_events ADD COLUMN IF NOT EXISTS previous_event_hash CHAR(64);
ALTER TABLE fde_audit_events ADD COLUMN IF NOT EXISTS event_hash CHAR(64);
CREATE INDEX IF NOT EXISTS idx_fde_idempotency_expiry ON fde_idempotency_keys(expires_at);
