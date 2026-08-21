# ADR 0024 — Privacy & Data Lifecycle Plane

## Status

Accepted

## Decision

Add explicit data classification, processing-purpose, retention, legal-hold and erasure contracts to the platform. Keep PII payloads outside the lifecycle contract and persistence boundary.

## Rationale

Enterprise AI systems need more than access control: privacy risk depends on what data is collected, why it is processed, how long it is retained and whether it can be deleted or selectively disclosed. GDPR guidance emphasizes purpose limitation, minimisation and storage limitation; NIST Privacy Framework models the complete data lifecycle; ISO/IEC 27701:2025 provides a current PIMS framework for PII controllers/processors.

## Security controls

- tenant-scoped asset identity;
- explicit purpose and classification;
- bounded retention policy;
- fail-closed legal hold;
- tenant-bound erasure request;
- deletion receipt without content duplication;
- integrity digest for receipt verification;
- timezone-aware timestamps;
- bounded metadata.

## Boundaries

The plane does not replace identity, authorization, persistence, audit or legal decision-making. Production adapters must execute erasure across every applicable data store and preserve only the minimum evidence necessary to demonstrate the action.
