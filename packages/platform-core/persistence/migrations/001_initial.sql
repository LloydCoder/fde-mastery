-- FDE Mastery Month 7 initial durable state schema.
-- Apply through the deployment migration mechanism; do not use this file as a
-- substitute for a migration framework's version tracking.

CREATE TABLE IF NOT EXISTS fde_clients (
    client_id VARCHAR(100) PRIMARY KEY,
    client_name VARCHAR(200) NOT NULL,
    domains VARCHAR(1000) NOT NULL,
    registered_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS fde_client_usage (
    client_id VARCHAR(100) PRIMARY KEY REFERENCES fde_clients(client_id) ON DELETE CASCADE,
    total_calls INTEGER NOT NULL DEFAULT 0 CHECK (total_calls >= 0),
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fde_client_usage_updated_at
    ON fde_client_usage(updated_at);
