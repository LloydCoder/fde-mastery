# Build 27 — Privacy & Data Lifecycle Plane

## Objective

Add an enterprise privacy boundary for data classification, purpose limitation, retention, legal holds and auditable erasure without storing PII inside the lifecycle contracts or creating a second persistence/authorization system.

## Research basis

The current European Commission GDPR guidance emphasizes purpose limitation, data minimisation and storage limitation: personal data should be collected only when necessary for a stated purpose and retained no longer than necessary. NIST's Privacy Framework treats the data lifecycle as collection, retention, logging, generation, transformation, use, disclosure, sharing, transmission and disposal, and its newer privacy guidance emphasizes granular management including alteration and deletion. ISO/IEC 27701:2025 is the current published privacy information management standard for PII controllers and processors.

## Delivered

- Tenant-scoped data assets.
- Explicit data classifications: public, internal, confidential, PII, sensitive PII.
- Explicit processing purposes.
- Version-independent retention policies with bounded retention windows.
- Policy-to-asset purpose matching.
- Retention-window deletion decisions.
- Legal-hold fail-closed behavior.
- Tenant-isolated erasure requests.
- Deletion receipt with SHA-256 integrity digest.
- No raw PII in receipts.
- Timezone-aware temporal validation.
- Bounded metadata/cardinality controls.
- Provider-neutral lifecycle boundary.

## Security and privacy model

The lifecycle plane does not decide user identity or authorization. Existing identity, tenant authorization and persistence boundaries remain authoritative. A missing retention policy, legal hold or invalid tenant/asset association fails closed.

The contracts record metadata about data assets rather than the data itself. Deletion receipts contain only identifiers and an integrity digest; they do not copy deleted content into the audit trail.

Sensitive PII is prohibited from the unqualified analytics purpose in this reference policy model. Production deployments may define additional lawful purposes and controls through policy configuration.

## Non-goals

- No claim of GDPR certification or legal advice.
- No DSAR workflow/UI.
- No data discovery scanner.
- No PII payload storage in the lifecycle registry.
- No replacement for the platform authorization engine.
- No replacement for production persistence adapters.
- No automated legal determination of whether a hold is valid.

## Verification

Build-specific tests cover tenant isolation, retention windows, legal holds, erasure receipts, policy/purpose integrity, sensitive-data purpose restrictions and timestamp validation. Repository CI remains the final merge gate for security, static analysis, SBOM, migrations, staging/load and production runtime validation.
