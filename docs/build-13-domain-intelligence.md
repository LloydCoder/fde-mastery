# Build 13 — Domain Intelligence Foundation

## Objective

Turn the existing domain adapters into a governed, machine-readable domain portfolio with a single promotion contract, representative evaluation fixtures, and a first-class Custom domain.

## What was already present

- Seven domain services were already routable.
- Procurement was already a native recommendation-only implementation.
- Cybersecurity, Finance, HealthTech, Logistics, Legal and RevOps were compatibility facades over isolated Month 1–6 implementations.
- Existing domain smoke coverage and high-impact human-review controls were already green.

Build 13 therefore does **not** rewrite the legacy domain engines. It establishes the missing promotion layer around them.

## Delivered

- Strengthened `DomainDescriptor` with lifecycle, risk, approval, evaluation and representative-data metadata.
- Added canonical `domains/registry.py` with lazy implementation factories.
- Added eight first-class domain registrations: Cybersecurity, Finance, HealthTech, Logistics, Legal, RevOps, Procurement and Custom.
- Added a native configuration-driven Custom domain with deterministic recommendation-only behavior and no autonomous side effects.
- Added synthetic representative promotion fixtures covering every domain.
- Added domain promotion contract tests covering catalog completeness, dataset coverage, factory loading, health, HITL requirements and fail-closed unknown-domain behavior.
- Registered Custom in the platform router while preserving existing resilience isolation.
- Added the Custom domain to the canonical `Domain` enum.

## Promotion contract

Every promoted domain must provide:

1. Stable canonical identifier and semantic version.
2. Explicit capabilities.
3. Lifecycle stage.
4. Risk classification.
5. Human-approval requirement.
6. Evaluation suite reference.
7. Representative evaluation data.
8. A loadable implementation factory.
9. Health metadata.
10. Capability metadata including human-in-the-loop behavior.

High and critical risk domains fail closed unless human approval is enabled in their descriptor.

## Architecture

```text
                    PLATFORM KERNEL
                          │
                 DomainDescriptor
                          │
                 ┌────────┴────────┐
                 │ Domain Registry │
                 └────────┬────────┘
                          │
          ┌───────────────┼────────────────┐
          │               │                │
     Legacy Facades   Native Domains   Custom Domain
          │               │                │
          └───────────────┼────────────────┘
                          │
                  Evaluation Fixtures
                          │
                    Promotion Gate
                          │
                       Customer
```

The registry remains outside `fde_platform`; the kernel owns only the provider-neutral descriptor contract. Domain implementations are loaded lazily so the kernel does not gain concrete infrastructure/provider dependencies.

## Security posture

- High-impact domain behavior remains human-controlled.
- Custom domains cannot directly execute tenant-defined side effects.
- Unknown domains fail closed.
- Domain metadata is validated before promotion/lookup.
- Representative fixtures are synthetic and contain no customer data.
- Existing policy, tool, model, tenant and audit boundaries remain authoritative.

## Research basis

The design follows lifecycle-based AI risk management: NIST AI RMF emphasizes governance, mapping, measurement and management across the AI lifecycle, while the Generative AI Profile highlights governance, content provenance, pre-deployment testing and incident disclosure. OWASP's 2026 Agentic Applications guidance likewise treats autonomous-agent security as a distinct, operational concern. The domain promotion contract makes these principles enforceable at the platform boundary rather than leaving them as documentation only.

## Verification

Build 13 is complete only after the repository's full Platform Quality workflow is green, including tests, security scans, migration validation, static analysis, SBOM validation, staging/load smoke and production Docker runtime smoke.

## Version

Platform version: **1.12.0**
