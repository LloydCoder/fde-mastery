# Build 20 — Incident & Reliability / SRE Plane

## Objective

Add a provider-neutral reliability control-plane foundation that turns existing observability and deployment primitives into explicit SLI/SLO/error-budget and incident-management contracts without introducing a second telemetry, deployment, authorization, or execution system.

## Research basis

The design was reviewed against:

- NIST SP 800-61 Rev. 3 (final April 2025), which integrates incident response into CSF 2.0 risk management and emphasizes preparation, detection, response and recovery.
- NIST Risk Management Framework Monitor guidance for continuous monitoring and ongoing assessment of control effectiveness.
- Google SRE guidance on user-centered SLIs/SLOs, error budgets and release-control policies.
- NIST AI RMF principles for continuous risk monitoring of AI systems.

Primary references:

- https://csrc.nist.gov/pubs/sp/800/61/r3/final
- https://csrc.nist.gov/projects/risk-management/about-rmf/monitor-step
- https://sre.google/sre-book/service-level-objectives/
- https://sre.google/workbook/error-budget-policy/
- https://www.nist.gov/itl/ai-risk-management-framework

## Delivered

- Typed SLI contracts with safe event-count validation and compliance calculation.
- Typed SLO contracts with explicit target and rolling-window semantics.
- Error-budget calculation with remaining budget, exhaustion and release-control recommendation.
- Explicit incident severity and lifecycle states.
- Fail-closed incident state transitions.
- Tenant binding on incident transitions.
- Tenant-scoped incident filtering.
- Timezone-aware timestamps for incident, postmortem and corrective-action records.
- Postmortem contract covering impact, root cause, contributing factors, detection gaps and follow-up actions.
- Corrective-action contract with owner, priority, due date and completion state.
- Tests for lifecycle, tenant isolation, invalid metrics, timezone correctness and error-budget policy.

## Architecture

`Existing Observability -> SLI -> SLO -> Error Budget -> Reliability Action -> Incident -> Postmortem -> Corrective Action`

The reliability module is intentionally side-effect free. Persistence, alert delivery, deployment control, notification and orchestration remain behind their existing platform boundaries.

## Security properties

- Tenant identity is required for incident records.
- Cross-tenant incident transitions fail closed.
- Tenant filtering is explicit rather than inferred from object lookup.
- Timestamps must be timezone-aware to avoid ambiguous incident ordering.
- Reliability policy is deterministic and does not allow model output to authorize deployment changes.

## Release policy

The error-budget recommendation is:

- below 80% consumed: normal operation;
- 80% or more consumed but not exhausted: freeze non-critical changes;
- exhausted: freeze changes except explicitly governed critical/security work.

This is a platform recommendation contract, not an automatic deployment action.

## Verification

Build 20 is green only after the full repository Platform Quality and Semgrep gates pass, including tests, security checks, static analysis, SBOM, staging/load smoke and production Docker runtime smoke.
