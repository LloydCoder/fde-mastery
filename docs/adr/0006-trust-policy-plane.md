# ADR 0006 — Trust & Policy Plane

## Status
Accepted — Build 5.

## Context
Builds 1–4 established platform boundaries, tenant-aware identity, agent execution and durable workflows. Enterprise AI execution now needs a centralized authorization boundary that can express least privilege, risk tiers, policy versions and human approval without coupling domain agents to an identity provider or policy engine.

## Decision
Introduce a framework-neutral trust plane with four responsibilities:

1. **Policy Decision Point (PDP)** — deterministic, fail-closed authorization decisions.
2. **Risk classification** — explicit LOW/MEDIUM/HIGH/CRITICAL tiers used as policy inputs.
3. **Human approval boundary** — high-risk or policy-designated operations require an explicit, expiring approval.
4. **Authorization audit** — append-oriented, tamper-evident decision records with policy version and risk context.

The PDP checks tenant isolation before policy evaluation, then request-level and rule-level roles/scopes, action/resource matching, risk limits, and approval requirements. Unknown actions and unmatched policies deny by default.

## Consequences

- Domain agents no longer need to implement bespoke authorization logic.
- Policy versions become observable and auditable.
- High-risk agent actions can pause at a human control boundary before Build 6 tool execution.
- The core remains provider-neutral; a future OPA/Cedar/remote PDP adapter can implement the same port.
- The reference approval store is intentionally in-memory; durable enterprise approval persistence will be provided by the platform adapter layer as infrastructure matures.

## Security basis

The design maps to OWASP ASVS 5.0 authorization requirements for documented, trusted-server authorization, least privilege and cross-tenant controls. It also follows NIST AI RMF/GAI guidance that governance, risk management and human oversight should be defined throughout the AI lifecycle.
