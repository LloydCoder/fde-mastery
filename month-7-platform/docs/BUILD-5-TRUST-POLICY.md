# Build 5 — Trust & Policy Plane

**Status: GREEN candidate — pending Platform Quality CI.**

## Scope

Build 5 establishes the enterprise authorization and AI governance boundary above the Agent Runtime and Durable Workflow Engine.

### Delivered

- Deterministic fail-closed Policy Decision Point (PDP).
- Versioned immutable policy rules.
- Explicit action/resource matching.
- Request-level and policy-level role/scope enforcement.
- Mandatory cross-tenant denial before rule evaluation.
- LOW/MEDIUM/HIGH/CRITICAL risk tiers.
- Risk-based and policy-based human approval requirements.
- Expiring, single-use approval reference store.
- Tamper-evident authorization audit event digest chaining.
- Architecture and security regression tests.

## Security properties

1. **Deny by default.** No matching policy means deny.
2. **Tenant first.** A policy can never grant access across tenant boundaries.
3. **Least privilege.** Roles and scopes are explicit inputs to every decision.
4. **Risk is additive.** Risk can require approval; it cannot bypass authorization.
5. **Human control.** HIGH/CRITICAL actions can require an explicit, expiring approval.
6. **Auditability.** Decisions carry policy version, risk and a tamper-evident digest.
7. **Provider neutrality.** The domain boundary does not depend on a specific policy engine.

## Architecture

```text
RequestContext
     |
     v
  Policy PDP -----> Risk classifier
     |
     +---- deny/allow
     |
     +---- approval required ----> Human Approval Boundary
     |
     v
Authorization Audit
     |
     v
Agent Runtime / Workflow
```

## Research basis

OWASP ASVS 5.0 V8 requires authorization rules to be documented, enforced at a trusted service layer, least-privileged, and protected against cross-tenant access. NIST AI RMF and the Generative AI Profile emphasize governance, risk management, documentation and human oversight for AI systems.

References:

- OWASP ASVS 5.0 Authorization: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x17-V8-Authorization.md
- OWASP Access Control guidance: https://owasp.org/www-community/Access_Control
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- NIST Generative AI Profile: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

CI gate: Platform Quality must pass before Build 5 is merged.
