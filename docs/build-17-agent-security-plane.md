# Build 17 — Advanced AI / Agent Security Plane

## Objective

Add runtime controls for autonomous and tool-using agents that address current agentic security risks while preserving the existing identity, policy, Tool Gateway, integration and approval boundaries.

## Delivered

- Risk-tiered agent action security gate.
- Explicit agent security context bound to tenant, agent and request.
- Capability allowlisting independent from model output.
- Confidence thresholds tied to action risk.
- Autonomy budget enforcement for external/irreversible actions.
- Human approval reference requirement for high/critical actions.
- Explicit rejection of irreversible actions from untrusted/external context.
- Deterministic prompt-injection screening as defense-in-depth.
- High-confidence credential/JWT/private-key output redaction.
- Memory provenance and trust levels with tenant-scoped filtering.
- Secure Tool Gateway decorator that blocks unsafe actions before the existing executor.
- No second authorization or execution engine was introduced.
- Security regression tests for prompt injection, sensitive-output leakage, memory poisoning boundaries, tenant mismatch, capability escalation and irreversible actions.

## Threat coverage

The design maps to current OWASP GenAI and Agentic guidance, including prompt injection, sensitive information disclosure, excessive agency, vector/context poisoning, memory/context poisoning, insecure inter-agent communication and human-agent trust exploitation. The gate treats model output as untrusted input and never converts a model decision directly into authorization.

## Architecture

```text
Agent / Model Output
        │
        ▼
  Agent Security Context
        │
        ├── Tenant
        ├── Agent identity
        ├── Trust level
        ├── Confidence
        ├── Capability budget
        └── Approval reference
        │
        ▼
 Agent Action Security Gate
        │
        ├── tenant check
        ├── capability check
        ├── confidence/risk check
        ├── autonomy budget
        └── approval / trust check
        │
        ▼
 Existing Tool Gateway
        │
        ▼
 Existing Policy / Approval / Idempotency
        │
        ▼
 External side effect
```

## Important boundary

Prompt-injection screening and output redaction are defense-in-depth controls. They are not treated as proof that content is safe. Authorization remains deterministic and platform-owned.

## Research basis

OWASP's 2026 Agentic Applications Top 10 identifies agent-specific risks including memory/context poisoning, insecure inter-agent communication, cascading failures, human-agent trust exploitation and rogue agents. OWASP's current GenAI guidance also continues to emphasize prompt injection, sensitive information disclosure, excessive agency, vector/embedding weaknesses and unbounded consumption. NIST's Generative AI Profile provides lifecycle-oriented risk management guidance.

## Version

Platform version: **1.16.0**
