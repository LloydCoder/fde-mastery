# ADR-0003: Identity and multi-tenancy boundary

- **Status:** Accepted
- **Build:** 2
- **Decision:** Establish tenant isolation as a platform invariant before adding durable agent execution.

## Context

FDE Mastery serves multiple organizations and supports users, services, and future agents. Authentication answers *who is this subject?*; authorization answers *may this subject perform this action?*; tenancy answers *which organization's resources may be addressed?* These concerns must remain explicit and independently testable.

## Decision

1. Use a provider-neutral `Principal` as the kernel identity representation.
2. Bind every authenticated request to an immutable `RequestContext` containing a tenant and environment.
3. Deny cross-tenant resource access before policy-specific checks.
4. Treat tenant, environment, subject, roles, and scopes as explicit authorization inputs.
5. Use PostgreSQL Row-Level Security as a second isolation boundary for tenant-owned persistence.
6. Set database tenant context only at the trusted application transaction boundary using `fde.tenant_id`.
7. Use restrictive RLS policies with both `USING` and `WITH CHECK`; enable and force RLS on the new tenant-owned tables.
8. Keep the existing OIDC implementation as an identity-provider adapter rather than making OIDC claims the domain model.
9. Preserve the existing security APIs during migration; new code consumes the kernel identity/authorization contracts.

## Rationale

NIST SP 800-207 places policy decision and enforcement around resource access and rejects implicit trust based on network location. PostgreSQL RLS provides a database-level row isolation boundary; when enabled without applicable policy it is default-deny, and `FORCE ROW LEVEL SECURITY` prevents ordinary table-owner bypass. This design therefore uses application authorization plus database isolation rather than relying on either layer alone.

## Non-goals

- Build 2 does not introduce a full external policy engine.
- Build 2 does not migrate every legacy persistence table to RLS.
- Build 2 does not implement service identity/SPIFFE.
- Build 2 does not introduce a new identity provider.

Those are later platform concerns and will consume the contracts established here.

## Consequences

Positive:

- tenant isolation becomes a platform invariant;
- domain code no longer needs to understand OIDC claim shapes;
- database enforcement provides defense in depth;
- future ABAC/risk policies can consume a stable request context;
- dedicated data planes can reuse the same identity model.

Trade-off:

- every tenant-scoped persistence operation must establish database tenant context;
- legacy tables require an explicit migration plan before RLS can safely be enabled on them.
