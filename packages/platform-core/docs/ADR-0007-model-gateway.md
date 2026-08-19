# ADR-0007: Governed Model Gateway

## Status

Accepted — Build 7.

## Context

Agent systems need a controlled boundary between application logic and external model providers. Direct provider SDK usage couples the platform to vendors and makes model allowlisting, data classification, routing, fallback, policy enforcement, provenance and operational controls inconsistent.

Model output is also untrusted input. A model gateway must therefore enforce constraints before invocation and must not treat a successful provider response as authorization to perform downstream actions.

## Decision

All platform-level model invocation crosses a framework-neutral `ModelGateway` boundary.

The gateway provides:

- immutable, versioned model definitions;
- explicit model capabilities;
- explicit data-class allowlists;
- a central model registry;
- named deterministic routes with ordered candidates;
- provider adapters that isolate SDKs and network clients;
- policy evaluation before provider invocation;
- bounded output-token requests;
- explicit response/error envelopes;
- retry-aware fallback that is limited to retryable provider failures.

## Security rationale

The model is not a policy authority. Authorization, tenant isolation and downstream action controls remain in the platform's identity and Trust & Policy layers. Model output must be validated before it can influence tools or other privileged components.

The design addresses OWASP GenAI risks including excessive agency, improper output handling, model supply-chain exposure and unbounded consumption. It also supports NIST AI RMF governance by providing an explicit inventory and control point for models used in production.

## Routing and fallback

Fallback is deterministic and allowlisted. The gateway does not fail over on authorization, policy, data-classification, capability or invalid-request failures. Those failures indicate that changing providers would not make the operation safe or valid.

Provider failures marked retryable may proceed to the next explicitly registered candidate. Production implementations should additionally enforce global retry budgets, rate limits, circuit breakers and provider-specific timeout policies.

## Consequences

Positive:

- centralized model governance;
- vendor-neutral application contracts;
- safer provider migration and controlled fallback;
- explicit data handling constraints;
- a natural integration point for telemetry, cost controls and evaluation gates in later builds;
- model inventory and provenance can be governed independently from provider SDKs.

Trade-offs:

- model integrations require adapters and explicit registration;
- the reference implementation is intentionally in-memory and does not yet provide durable routing state or production telemetry;
- advanced routing based on latency, quality or cost belongs in later observability/evaluation work rather than being hidden inside the kernel.
