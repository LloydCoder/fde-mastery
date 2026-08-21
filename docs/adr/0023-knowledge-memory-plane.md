# ADR 0023 — Enterprise Knowledge & Memory Plane

## Status

Accepted

## Decision

Introduce a provider-neutral knowledge/memory contract with explicit tenant scope, provenance/trust, integrity, retention and retrieval policy boundaries.

## Rationale

Persistent context materially increases agent utility but also creates a durable attack surface. OWASP ASI06 identifies Memory & Context Poisoning as a distinct agentic risk. The platform therefore treats memory as untrusted data with explicit trust promotion rather than allowing persistence to imply authority.

## Boundaries

The plane owns memory/knowledge contracts and retrieval eligibility. Existing identity, authorization, policy, Tool Gateway, persistence and observability systems remain authoritative. Vector indexing, embeddings, ranking and model providers remain replaceable implementations behind ports.

## Security controls

- tenant + scope isolation;
- explicit trust levels;
- fail-closed retrieval defaults;
- external content opt-in;
- deterministic poisoning signal;
- explicit override for poisoned records;
- SHA-256 content integrity digest;
- monotonically increasing record versions;
- expiration enforcement;
- bounded metadata/tags;
- timezone-aware temporal state.

## Limitations

Instruction-pattern screening is a deterministic signal, not a complete prompt-injection detector. It must be combined with model-level safeguards, policy enforcement, least privilege and human approval for consequential actions.
