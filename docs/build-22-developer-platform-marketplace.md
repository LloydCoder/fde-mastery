# Build 22 — Developer Platform & Marketplace

## Objective

Provide a provider-neutral, tenant-safe extension control plane for third-party developer extensions without allowing marketplace metadata to become an execution or authorization bypass.

## Implemented

- Strict extension identifiers and SemVer validation.
- Explicit capability taxonomy.
- Dangerous `platform.admin` capability isolated from other capabilities.
- Artifact SHA-256 binding.
- SLSA-compatible provenance subject binding.
- HTTPS-only provenance/source references.
- Ed25519 signature envelopes with trusted-key verification.
- Canonical, deterministic manifest bytes for signing and verification.
- Malformed-signature fail-closed handling.
- Publisher allowlisting.
- API compatibility bounds.
- Required-capability promotion gates.
- Fail-closed promotion decisions.
- Tenant-scoped extension registry.
- Immutable extension identity within a tenant.
- Explicit submitted → approved promotion boundary.
- No extension code execution in the marketplace layer.

## Supply-chain design

The design follows current OCI/Sigstore/SLSA patterns rather than inventing a proprietary artifact model. OCI 1.1 supports subject-linked artifacts and the Referrers API, which is appropriate for associating signatures and attestations with an immutable artifact digest. Sigstore bundles package verification material and signature content, while SLSA provenance binds an artifact to its build inputs and builder.

References:

- https://opencontainers.org/posts/blog/2024-03-13-image-and-distribution-1-1/
- https://docs.sigstore.dev/about/bundle/
- https://slsa.dev/spec/draft/provenance

## Security boundary

The marketplace is a control-plane admission layer. A manifest being approved does **not** authorize a tool call or execute code. Runtime authorization remains owned by the existing policy/authorization and Tool Gateway boundaries.

The resulting flow is:

`Extension Artifact → Digest → Provenance → Signature → Publisher Trust → Capability Policy → API Compatibility → Human/Control-Plane Promotion → Existing Runtime Authorization`

## Verification

Build 22 is complete only after the repository Platform Quality, SDK Quality, Semgrep, production Docker/runtime, SBOM, migration, security, static-analysis and build-specific extension tests are green. A transient infrastructure failure must be rerun and independently verified; it must never be treated as a passing gate.
