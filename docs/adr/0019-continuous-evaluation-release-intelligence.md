# ADR 0019 — Continuous Evaluation & Release Intelligence

## Status

Accepted — Build 18.

## Context

FDE MASTERY already contains golden/adversarial/safety/quality/cost evaluation gates and statistical drift detection. A production platform also needs a single deterministic decision contract that combines those signals before a candidate is promoted.

## Decision

Add a release-assessment layer under the existing evaluation package. It consumes immutable tenant-scoped evaluation evidence and produces one of three decisions: `PROMOTE`, `BLOCK`, or `ROLLBACK`.

The evaluator does not deploy software. Deployment remains owned by the existing deployment/control-plane boundaries.

Promotion requires:

- explicit passed evaluation status;
- minimum pass rate;
- metric thresholds;
- no statistically significant regression according to the existing drift detector;
- passing security evaluation;
- cost and latency regression within configured limits;
- explicit evidence identifiers.

Catastrophic quality or security failure produces `ROLLBACK` so an external release controller can invoke the existing rollback mechanism.

## Consequences

Positive:

- one auditable release decision contract;
- deterministic fail-closed behavior;
- tenant and target isolation;
- explicit evaluator version and evidence lineage;
- reusable across models, agents, policies, and domain workflows;
- no second deployment executor.

Trade-off:

- release policy thresholds must be configured per risk profile rather than assumed universally.

## Security

The evaluator never treats model output as authorization. Security evidence is an independent gate, and high-impact actions remain subject to the existing policy and approval planes.
