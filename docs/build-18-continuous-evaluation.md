# Build 18 — Continuous Evaluation & Release Intelligence

## Objective

Turn the existing Build 9 evaluation plane into a deterministic continuous-evaluation release gate without introducing a second deployment runtime.

## Research basis

Build 18 follows a risk-based lifecycle approach: evaluation is part of design, deployment, use, and ongoing monitoring rather than a one-time benchmark. NIST AI RMF and its Generative AI Profile emphasize measurement, evaluation, verification, validation, and lifecycle risk management. OWASP's 2026 agentic guidance emphasizes continuous monitoring, behavioral baselines, validation of agent intent, and explicit controls around high-impact actions.

## Delivered

- Immutable, tenant-scoped `EvaluationRun` contract.
- Versioned evaluator identity and explicit evidence references.
- Metric thresholds with baseline/current values.
- Pass-rate release threshold.
- Cost regression guardrail.
- Latency regression guardrail.
- Existing statistical drift detector integrated into release assessment.
- Security evaluation gate.
- Fail-closed `PROMOTE` / `BLOCK` / `ROLLBACK` decision.
- Catastrophic quality/security failures produce rollback decisions rather than promotion.
- Tenant/target-scoped run comparison.
- Deterministic evidence aggregation.
- Promotion helper that refuses non-promotable assessments.
- Tests for happy path, security failure, quality regression, cost/latency regression, evidence requirements, scope isolation, and invalid policy configuration.

## Architectural boundary

The release evaluator decides whether a candidate is eligible for promotion. It does not deploy, mutate production state, or bypass the existing deployment, policy, workflow, or human-approval boundaries.

Flow:

`EvaluationRun -> ReleasePolicy -> Drift + Metrics + Security -> ReleaseAssessment -> existing deployment/policy boundary`

## Verification

Build 18 is green only after the repository's complete Platform Quality gate passes, including tests, security checks, migration validation, static analysis, SBOM validation, staging/load smoke, production Docker runtime smoke, and Semgrep.

## Standards alignment

- NIST AI RMF / NIST AI RMF Generative AI Profile.
- NIST GenAI evaluation and TEVV direction.
- OWASP Top 10 for Agentic Applications 2026.
- Existing FDE MASTERY evaluation, observability, policy, deployment, and durable-workflow architecture.
