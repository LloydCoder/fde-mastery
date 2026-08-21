# ADR 0025 — Enterprise Identity Governance Plane

## Status

Accepted

## Decision

Add explicit role, permission and delegated-binding contracts with tenant/scope boundaries and provisioning-change idempotency. Keep authentication and final authorization in the existing identity and policy boundaries.

## Rationale

Enterprise FDE deployments need controlled privilege assignment, delegation and deprovisioning. NIST Zero Trust guidance requires policy-driven, risk-based access with least privilege, while OWASP recommends server-side authorization and strict multi-tenant segregation.

## Security controls

- tenant + scope binding;
- expiry and revocation;
- bounded permissions and role cardinality;
- idempotent provisioning changes;
- timezone-aware timestamps;
- fail-closed unknown-role handling;
- final authorization delegated to the existing PDP.

## Compatibility

The contract is provider-neutral. OIDC, SAML, SCIM and enterprise directories can map into these contracts through adapters without coupling the kernel to an identity vendor or protocol server.
