# Build 26 — Enterprise Knowledge & Memory Plane

## Objective

Provide a tenant- and engagement-scoped trust boundary for durable knowledge and agent memory without creating a second persistence, vector, retrieval, authorization or LLM platform.

## Research basis

OWASP's 2026 Agentic Applications guidance identifies Memory & Context Poisoning as a distinct risk: attacker-controlled or partially validated content can persist into memory, summaries, embeddings or RAG stores and influence future reasoning and tool use. NIST AI RMF and its Generative AI Profile emphasize documented data provenance, context, risk controls and ongoing measurement. OpenAI's current knowledge-retrieval reference architecture emphasizes grounded answers with citations and evaluations.

## Delivered

- Tenant-scoped records.
- Engagement/project scope binding.
- Explicit trust levels: untrusted, external, user, verified.
- Fail-closed retrieval policy.
- External-memory opt-in.
- Poisoning detection for high-confidence instruction-injection patterns.
- Explicit policy override required for poisoned records.
- SHA-256 content integrity digest.
- Immutable version ordering.
- Expiration/retention boundary.
- Timezone-aware temporal validation.
- Bounded metadata and tag cardinality.
- Provider-neutral storage/indexing boundary.

## Security model

Retrieved knowledge is data, not authorization. The memory layer cannot grant permissions, approve tools, change policy or elevate agent autonomy. Trust level and retrieval policy only determine whether a record may enter an agent's context.

Tenant and scope checks occur before retrieval. Untrusted/external content is excluded by default. Poisoned content is excluded by default and requires an explicit policy decision to retrieve. Content digests provide tamper detection but are not a signature or provenance attestation; authoritative provenance remains an application responsibility.

## Non-goals

- No vector database.
- No embedding provider.
- No semantic ranking model.
- No LLM-generated summaries.
- No replacement for the existing Tool Gateway or authorization service.
- No claim that regex screening catches all prompt injection or poisoning.

## Verification

Build-specific tests cover tenant isolation, scope isolation, trust policy, poisoning controls, explicit override, expiration, digest integrity, version monotonicity and timezone validation. Repository CI remains the final gate for security, static analysis, SBOM, migration, staging/load and production runtime validation.
