# Build 29 — Secrets & Cryptographic-Key Lifecycle Plane

## Objective

Add a provider-neutral metadata and policy boundary for secrets and cryptographic keys. The kernel never stores or transports secret material; it stores references to an external vault/KMS and governs tenant/scope access, rotation and revocation.

## Research basis

OWASP's Secrets Management guidance recommends centralized storage, least-privilege access, automated rotation, revocation, expiration and lifecycle metadata. NIST SP 800-57 defines key management across the full lifecycle and treats key metadata as essential to selecting and controlling cryptographic keys.

## Delivered

- Secret/key reference contracts without secret material.
- Secret type classification.
- Lifecycle states: active, rotation due, rotating, revoked, expired.
- Tenant-scoped external references.
- Consumer/purpose metadata.
- Time-bounded access grants.
- Tenant + scope + subject access decisions.
- Rotation due enforcement.
- Rotation timestamp reset after successful rotation.
- Irreversible revocation state.
- Expiration enforcement.
- Bounded metadata.
- Timezone-aware lifecycle timestamps.
- Provider-neutral vault/KMS adapter boundary.

## Security model

The platform does not accept plaintext secret values. Access decisions fail closed for unknown, revoked, expired or rotation-due secrets. Grants are short-lived and bound to tenant, subject and scope. The external secret manager remains responsible for storing and returning the actual secret material.

## Non-goals

- No secret vault implementation.
- No plaintext secret persistence.
- No cryptographic primitive implementation.
- No replacement for existing authorization/policy enforcement.
- No provider lock-in to Vault, AWS, Azure or GCP.

## Verification

Build-specific tests cover tenant/scope isolation, revocation, expiry, rotation enforcement, rotation-window reset, grant idempotency and timestamp validation. Full repository CI remains the merge gate.
