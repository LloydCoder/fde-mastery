# ADR 0020 — Incident & Reliability / SRE Plane

## Decision

Add deterministic, provider-neutral SLI/SLO/error-budget and incident evidence contracts while keeping telemetry, authorization, deployment and durable execution behind their existing boundaries.

## Rationale

The design follows current SRE practice around user-facing SLIs, SLOs and error budgets, and NIST incident-response guidance emphasizing preparation, detection, response and recovery.

The platform returns a reliability recommendation; it does not let a model or reliability calculation directly authorize deployment changes.

## Safety

- tenant identity is mandatory;
- timestamps are timezone-aware;
- invalid metric counts fail closed;
- exhausted budgets produce a deterministic freeze recommendation;
- incident execution remains outside the contract package.
