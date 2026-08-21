# Build 23 — Enterprise Governance & Compliance Plane

## Research basis

Build 23 operationalizes governance rather than claiming certification. NIST AI RMF organizes AI risk work into Govern, Map, Measure and Manage and treats governance as cross-cutting throughout the lifecycle. The current NIST AI RMF Playbook was updated June 10, 2026 and the framework is being revised.

NIST AI 600-1 provides the Generative AI profile. ISO/IEC 42001:2023 specifies requirements for establishing, implementing, maintaining and continually improving an AI Management System and uses a management-system/PDCA approach.

Primary references:

- https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-risk-management-framework
- https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook
- https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- https://www.iso.org/standard/42001

## Implemented

- Provider-neutral framework identifiers for NIST AI RMF, NIST GenAI Profile, ISO/IEC 42001 and SOC 2.
- Explicit control records with owner, severity and required evidence types.
- Tenant-bound evidence records.
- SHA-256 evidence content binding.
- HTTPS evidence source requirement.
- Evidence freshness/expiry/revocation semantics.
- Timezone-aware assessment timestamps.
- Evidence-backed passing attestations.
- Rationale requirement for failed attestations.
- Tenant-isolated attestation lookup.
- Compliance posture scoring.
- Fail-closed audit-readiness calculation.
- Deterministic audit-pack serialization.
- Data-classification policy contract for model access.
- Higher-classification fail-closed model permission checks.
- Human-review and export policy flags.

## Boundary

This is a governance control plane, not a certification engine. A `PASS` means the configured control has current evidence and an attestation in this platform; it does not mean an external auditor has certified the organization.

Existing authorization, policy, Tool Gateway, Model Gateway, evaluation and incident systems remain the enforcement/runtime boundaries.

## Verification target

Build 23 is only GREEN after the complete repository Platform Quality + SDK Quality + Semgrep gates pass, including build-specific governance tests, security/static analysis, migration validation, SBOM validation, staging/load smoke and production Docker/runtime smoke.
