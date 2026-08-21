-- Build 15: tenant-scoped enterprise integration control plane.
-- Credential material is intentionally absent. credential_ref points to a managed secrets backend.

CREATE TABLE IF NOT EXISTS fde_integrations (
    integration_id UUID PRIMARY KEY,
    tenant_id VARCHAR(63) NOT NULL,
    environment VARCHAR(32) NOT NULL
        CHECK (environment IN ('development', 'staging', 'production')),
    provider VARCHAR(200) NOT NULL,
    provider_version VARCHAR(64) NOT NULL,
    auth_method VARCHAR(32) NOT NULL
        CHECK (auth_method IN ('api_key', 'oauth2', 'hmac', 'mtls', 'none')),
    credential_ref VARCHAR(500),
    capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    allowed_hosts JSONB NOT NULL DEFAULT '[]'::jsonb,
    webhook_events JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'disabled', 'degraded', 'revoked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fde_integrations_auth_ref_required
        CHECK (auth_method = 'none' OR credential_ref IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fde_integrations_tenant_env_id
    ON fde_integrations(tenant_id, environment, integration_id);
CREATE INDEX IF NOT EXISTS idx_fde_integrations_tenant_status
    ON fde_integrations(tenant_id, environment, status);
CREATE INDEX IF NOT EXISTS idx_fde_integrations_provider
    ON fde_integrations(provider, provider_version);

ALTER TABLE fde_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE fde_integrations FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS fde_integrations_tenant_isolation ON fde_integrations;
CREATE POLICY fde_integrations_tenant_isolation
    ON fde_integrations
    AS RESTRICTIVE
    FOR ALL
    USING (tenant_id = fde_current_tenant_id())
    WITH CHECK (tenant_id = fde_current_tenant_id());

CREATE TABLE IF NOT EXISTS fde_webhook_deliveries (
    delivery_id VARCHAR(255) NOT NULL,
    integration_id UUID NOT NULL REFERENCES fde_integrations(integration_id) ON DELETE CASCADE,
    tenant_id VARCHAR(63) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status VARCHAR(32) NOT NULL DEFAULT 'accepted'
        CHECK (status IN ('accepted', 'processed', 'failed', 'rejected')),
    PRIMARY KEY (integration_id, delivery_id)
);

CREATE INDEX IF NOT EXISTS idx_fde_webhook_deliveries_tenant
    ON fde_webhook_deliveries(tenant_id, received_at);

ALTER TABLE fde_webhook_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE fde_webhook_deliveries FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS fde_webhook_deliveries_tenant_isolation ON fde_webhook_deliveries;
CREATE POLICY fde_webhook_deliveries_tenant_isolation
    ON fde_webhook_deliveries
    AS RESTRICTIVE
    FOR ALL
    USING (tenant_id = fde_current_tenant_id())
    WITH CHECK (tenant_id = fde_current_tenant_id());

COMMENT ON TABLE fde_integrations IS
    'Tenant-scoped integration metadata. Secrets are external and referenced only by credential_ref.';
COMMENT ON TABLE fde_webhook_deliveries IS
    'Inbound webhook replay/idempotency ledger keyed by integration and provider delivery id.';
