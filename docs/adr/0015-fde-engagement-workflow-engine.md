# ADR-0015 — FDE Engagement & Workflow Engine

## Decision

Introduce a provider-neutral FDE engagement lifecycle above the existing durable workflow runtime. The lifecycle captures customer objective, workflow identity, baseline/value metrics, acceptance criteria, evidence, stage transitions and explicit promotion gates.

The new layer is a control-plane contract. It does not execute tools, models or external side effects. Durable execution remains delegated to the existing workflow runtime; authorization, policy, approvals, audit and evaluation remain authoritative at their existing boundaries.

## Lifecycle

```text
Discovery → Workflow Mapping → Value Case → Architecture → Build
→ Evaluation → Pilot → Shadow → Production → Operate → Transfer → Retired
```

Pilot may promote directly to Production only when the required evidence and approval gates are satisfied. Shadow mode is available for a safer controlled transition.

## Gates

- Discovery/workflow mapping require requirements evidence.
- Value case requires a reproducible baseline.
- Architecture/build require design evidence.
- Evaluation requires evaluation evidence.
- Pilot, shadow, production and transfer require explicit human approval evidence.
- Production additionally requires deployment evidence.
- Operate requires operational evidence.
- Transfer requires handoff and operations evidence.

## Security boundaries

The lifecycle never treats model output as authorization. It cannot execute tools or change external state. High-impact promotion stages require explicit approval evidence. Engagements are tenant-scoped and promotion reports expose tenant identity for audit correlation.

## Research basis

The design follows the production FDE delivery loop of qualifying a real workflow, defining measurable value, designing/building, evaluating, piloting, deploying, transferring and operating the resulting service. NIST AI RMF recommends managing AI risk across Govern, Map, Measure and Manage and testing systems before deployment and regularly during operation. OWASP's 2026 Agentic Applications work treats agentic security as a lifecycle concern requiring operational controls.

## Consequences

Positive:

- Customer engagements become explicit, versionable platform objects.
- Value and acceptance criteria become machine-readable.
- Promotion becomes evidence-driven rather than informal.
- Existing durable workflow infrastructure is reused instead of duplicated.
- Domain implementations remain independent of customer engagement state.

Trade-off:

- Persistent engagement storage and customer-facing control-plane APIs are intentionally deferred to later enterprise-control-plane work. This build establishes the provider-neutral contract first.

## Version

Platform version: **1.13.0**
