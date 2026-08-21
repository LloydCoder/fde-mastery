# Build 28 — Enterprise Identity Governance Plane

## Objective

Add a tenant-scoped identity-governance boundary for roles, permissions, delegated bindings, service/group subjects and provisioning lifecycle without replacing the existing authentication or policy decision point.

## Research basis

NIST's Zero Trust Architecture treats authentication and authorization as discrete functions and recommends continuous, policy-driven, risk-based evaluation. NIST SP 1800-35 also identifies enhanced identity governance and ICAM as core enterprise capabilities. OWASP recommends least privilege, server-side authorization and multi-tenant segregation; it also notes that ABAC/ReBAC can be more expressive than a flat RBAC model as enterprise complexity grows.

## Delivered

- Explicit subject types: user, group, service account.
- Version-independent role contracts.
- Fine-grained resource/action permissions.
- Tenant + scope-bound role bindings.
- Binding expiry.
- Immediate binding revocation.
- Effective-permission projection for the existing PDP boundary.
- Provisioning-change contracts with idempotency protection.
- Bounded role, permission and metadata cardinality.
- Timezone-aware lifecycle timestamps.
- Provider-neutral contract: SCIM/IdP connectors remain adapters rather than kernel dependencies.

## Security model

This plane is not an authorization replacement. It computes governed role/permission state for the existing policy decision point. A role binding never grants access outside its tenant and scope, and expired/revoked bindings are excluded. The final authorization decision remains server-side and fail-closed.

## Non-goals

- No password or credential storage.
- No replacement for OIDC/SAML authentication.
- No second authorization engine.
- No direct SCIM network server in the platform kernel.
- No client-side enforcement.
- No automatic privilege escalation.

## Verification

Build-specific tests cover tenant/scope isolation, expiry, revocation, unknown roles, duplicate bindings, provisioning idempotency and timestamp validation. Full repository CI remains the merge gate.
