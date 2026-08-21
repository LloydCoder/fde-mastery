# ADR 0026 — Secrets & Cryptographic-Key Lifecycle Plane

## Status

Accepted

## Decision

Introduce provider-neutral secret/key references and lifecycle/access contracts while keeping secret material in an external vault/KMS.

## Rationale

Secrets are authorization material and must be managed through least-privilege access, rotation, revocation and expiration. OWASP recommends centralized lifecycle management; NIST SP 800-57 treats key management as a complete lifecycle including generation, storage, use and destruction.

## Security controls

- no plaintext secret material in the platform contracts;
- tenant-bound external references;
- short-lived, scope-bound access grants;
- rotation-due fail-closed behavior;
- irreversible revocation;
- explicit expiration;
- bounded metadata;
- timezone-aware timestamps.

## Boundaries

Vault/KMS providers remain adapters. Existing identity and authorization systems remain authoritative. This plane provides lifecycle policy and access intent, not cryptographic storage or cryptographic implementation.
