# P0–P2 Enterprise Platform Upgrade

This document records the implemented platform boundaries introduced after the enterprise architecture review.

## P0 — Control, execution and isolation

- Versioned Agent/Tool/Model/Policy registries with immutable versions and explicit promotion states.
- Durable workflow queue contract with leases, acknowledgements and idempotency keys.
- Deployable worker boundary outside the API process.
- Independent trust-plane security gateway; high-impact actions fail closed into approval.
- Quorum/expiry human approvals.
- Tenant-aware identity context and PostgreSQL RLS foundations.
- Explicit sandbox policy for custom/untrusted workloads.

## P1 — Interoperability and operations

- Authorization-aware MCP tool-call contracts.
- Authorization-aware A2A message envelopes; agent permissions do not implicitly transfer.
- Decision lineage based on auditable evidence references, never hidden chain-of-thought.
- Tenant-aware FinOps for model tokens, tool cost and compute cost.
- AI incident lifecycle with controlled state transitions.
- Existing transactional outbox/inbox/event contracts remain the reliable integration boundary.

## P2 — Platform productization

- Shared, isolated and dedicated deployment profiles.
- `platformctl manifest` for machine-readable capabilities.
- `platformctl doctor` for executable import/readiness checks that fail closed.
- CI compilation and tests cover the new platform boundaries.
- The platform remains a modular monolith until independent scaling/isolation creates a justified service boundary.

## Verification

The Platform Quality workflow explicitly runs the P0–P2 test suite, compiles the CLI and worker boundaries, and executes `platformctl doctor` and `platformctl manifest` before the staging API, load, SBOM and container gates.
