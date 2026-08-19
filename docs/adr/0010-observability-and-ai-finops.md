# ADR 0010 — Observability & AI FinOps

- **Status:** Accepted
- **Date:** 2026-08-19
- **Build:** 10

## Context

Enterprise AI execution needs correlated traces, metrics and events across agents, workflows, models, tools and asynchronous messaging. AI workloads additionally require tenant-scoped cost accounting, latency measurement and explicit budget guardrails. Telemetry must not become a data-exfiltration path: prompts, completions, tool arguments and results can contain sensitive information and therefore require explicit opt-in handling.

## Decision

FDE Mastery establishes a framework-neutral observability boundary with adapters for OpenTelemetry and other backends. The platform records low-cardinality operational observations and metrics, with stable names and bounded attributes. GenAI telemetry follows OpenTelemetry GenAI semantic conventions where applicable, including model identity and token usage, while sensitive content remains opt-in.

AI FinOps is a separate policy/measurement concern. Every cost record is tenant-scoped and associated with an execution run and model. Budgets are explicit and fail closed before a new record would exceed the configured limit. Production persistence remains behind an adapter boundary.

The platform does not claim exactly-once billing. Cost events must be idempotently correlated with execution identifiers when persisted by a production adapter.

## Consequences

Positive:

- end-to-end execution can be correlated across synchronous and asynchronous boundaries;
- model latency and token usage become measurable;
- tenant cost attribution is explicit;
- budgets can prevent uncontrolled AI spend;
- telemetry backend choice remains replaceable;
- sensitive GenAI content is not required for baseline observability.

Trade-offs:

- semantic conventions evolve and adapters require controlled upgrades;
- cardinality and retention need operational governance;
- token usage does not by itself equal provider invoice cost;
- distributed cost accounting requires durable idempotency and reconciliation.

## Standards basis

OpenTelemetry Semantic Conventions provide common names and structures for telemetry signals, including messaging and GenAI operations. The OpenTelemetry GenAI guidance specifically exposes model, token and latency telemetry while warning that message content can contain sensitive information. NIST AI RMF and its Generative AI Profile provide the governance context for trustworthy measurement and monitoring.
