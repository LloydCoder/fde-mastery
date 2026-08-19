# Build 2 — Identity & Multi-Tenancy

**Status: implementation complete; CI is the release gate.**

## Scope

Build 2 establishes identity and tenant isolation as platform invariants without coupling the kernel to an identity provider.

### Delivered

- Provider-neutral `Principal` model for users, services, and agents.
- Canonical `TenantRef` and explicit development/staging/production environments.
- Immutable `RequestContext` binding principal, tenant, environment, and request ID.
- Fail-closed authorization service with explicit tenant/resource checks, scopes, and roles.
- PostgreSQL tenant, environment, and membership tables.
- PostgreSQL RLS with `FORCE ROW LEVEL SECURITY`, restrictive policies, and both `USING`/`WITH CHECK` tenant predicates.
- Regression tests for cross-tenant denial, scope enforcement, context binding, and migration controls.
- ADR-0003 documenting the identity and tenancy boundary.

## Security model

```text
OIDC / API-key / service identity adapter
                    ↓
              Principal
                    ↓
             RequestContext
                    ↓
        tenant + environment binding
                    ↓
        authorization / policy checks
                    ↓
             resource access
                    ↓
        PostgreSQL RLS defense-in-depth
```

The database tenant context is established by the trusted application transaction boundary. A tenant identifier supplied by an untrusted request is never treated as an authorization decision.

## Migration boundary

Existing legacy persistence tables are intentionally not forced into RLS in Build 2 because they do not yet carry a canonical tenant key. They remain covered by the existing application authorization model. Future builds will migrate tenant-owned resources table-by-table, backfill tenant ownership, validate isolation, and only then enable RLS.

## Standards basis

The design follows the identity-centric zero-trust model in NIST SP 800-207/800-207A and PostgreSQL's current row-security semantics. RLS is a defense-in-depth boundary, not a replacement for application authorization.
