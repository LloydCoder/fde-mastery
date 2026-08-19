-- Build 2: identity and tenancy foundation.
--
-- Design notes:
-- * tenant_id is the primary application isolation boundary.
-- * environment_id separates development/staging/production within a tenant.
-- * membership rows bind subjects to tenants and roles.
-- * PostgreSQL RLS is default-deny when enabled without a matching policy.
-- * fde.tenant_id is set by the trusted application transaction boundary; it is
--   never accepted from arbitrary SQL/user input as an authorization decision.

CREATE TABLE IF NOT EXISTS fde_tenants (
    tenant_id VARCHAR(63) PRIMARY KEY,
    display_name VARCHAR(200) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'suspended', 'deleted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fde_tenant_environments (
    tenant_id VARCHAR(63) NOT NULL REFERENCES fde_tenants(tenant_id) ON DELETE CASCADE,
    environment VARCHAR(32) NOT NULL
        CHECK (environment IN ('development', 'staging', 'production')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, environment)
);

CREATE TABLE IF NOT EXISTS fde_tenant_memberships (
    tenant_id VARCHAR(63) NOT NULL REFERENCES fde_tenants(tenant_id) ON DELETE CASCADE,
    subject VARCHAR(255) NOT NULL,
    principal_type VARCHAR(32) NOT NULL
        CHECK (principal_type IN ('user', 'service', 'agent')),
    roles TEXT[] NOT NULL DEFAULT '{}',
    scopes TEXT[] NOT NULL DEFAULT '{}',
    status VARCHAR(32) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'suspended', 'revoked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, subject)
);

CREATE INDEX IF NOT EXISTS idx_fde_memberships_subject
    ON fde_tenant_memberships(subject);

CREATE OR REPLACE FUNCTION fde_current_tenant_id()
RETURNS VARCHAR
LANGUAGE SQL
STABLE
AS $$
    SELECT NULLIF(current_setting('fde.tenant_id', true), '')
$$;

ALTER TABLE fde_tenant_environments ENABLE ROW LEVEL SECURITY;
ALTER TABLE fde_tenant_environments FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS fde_environment_tenant_isolation ON fde_tenant_environments;
CREATE POLICY fde_environment_tenant_isolation
    ON fde_tenant_environments
    AS RESTRICTIVE
    FOR ALL
    USING (tenant_id = fde_current_tenant_id())
    WITH CHECK (tenant_id = fde_current_tenant_id());

ALTER TABLE fde_tenant_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE fde_tenant_memberships FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS fde_membership_tenant_isolation ON fde_tenant_memberships;
CREATE POLICY fde_membership_tenant_isolation
    ON fde_tenant_memberships
    AS RESTRICTIVE
    FOR ALL
    USING (tenant_id = fde_current_tenant_id())
    WITH CHECK (tenant_id = fde_current_tenant_id());

COMMENT ON FUNCTION fde_current_tenant_id() IS
    'Trusted transaction-scoped tenant context used by RLS policies. The application must set this before tenant-scoped DB work.';
