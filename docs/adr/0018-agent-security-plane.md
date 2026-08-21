# ADR-0018 — Advanced AI / Agent Security Plane

## Status

Accepted — Build 17.

## Context

Model output, retrieved context, external tool responses and peer-agent messages are untrusted inputs. Existing policy and Tool Gateway controls provide deterministic authorization, but agentic systems also need a pre-action trust boundary that accounts for risk, confidence, autonomy and provenance.

## Decision

Add an agent security context and fail-closed action gate before the existing Tool Gateway. The gate checks tenant binding, capability grants, risk-adjusted confidence, autonomy budget, human approval references and trust level. It does not execute tools or replace the PDP.

Add deterministic defense-in-depth controls for prompt-injection indicators, credential-shaped output and memory provenance. These controls produce signals/redactions; they are never treated as authorization.

## Consequences

Positive:

- Agent decisions cannot silently expand their capability scope.
- High-risk actions require explicit approval evidence.
- Untrusted context cannot directly perform irreversible actions.
- Memory can be filtered by tenant and provenance/trust.
- Sensitive credential-shaped outputs are blocked at the output boundary.

Trade-offs:

- Pattern-based prompt-injection detection is necessarily incomplete and must remain supplemental.
- Risk inference from generic ToolCapability metadata is conservative and should be enriched by domain policy for specialized actions.
- Production deployments should persist security decisions/audit evidence through the existing authorization audit plane.

## Research references

- OWASP Top 10 for Agentic Applications 2026.
- OWASP GenAI LLM Top 10 2026.
- NIST AI RMF Generative AI Profile.
