# Build 7 — Model Gateway

## Objective

Create a single governed boundary for model invocation so agents do not call vendor SDKs directly and every model execution is subject to model inventory, capability, data-classification and policy controls.

## Delivered

- `ModelDefinition` — immutable model/provider metadata
- `ModelCapability` — explicit capability allowlist
- `DataClass` — request data classification
- `ModelRegistry` — explicit model/version inventory and named routes
- `ModelProvider` — provider-neutral adapter contract
- `ModelGateway` — routing and policy enforcement boundary
- retry-aware ordered fallback
- explicit `ModelResponse` and error codes
- policy hook before provider execution
- model output-token limit enforcement
- deterministic in-memory test adapters
- security regression tests

## Security controls

| Control | Enforcement |
|---|---|
| Model allowlisting | Registry rejects unknown route candidates |
| Version pinning | Model key is `name@version` |
| Capability control | Required capabilities must be declared by the model |
| Data isolation | Request data class must be permitted by the model |
| Authorization | Existing Trust & Policy layer remains upstream |
| Policy hook | Evaluated before provider invocation |
| Fallback safety | Only retryable provider failures may fail over |
| Output limits | Request cannot exceed model output budget |
| Provider isolation | SDKs stay behind `ModelProvider` adapters |
| Output trust | Model output is not treated as authorization |

## Non-goals

Build 7 does not yet implement provider-specific SDKs, durable model inventory storage, adaptive quality/cost routing, distributed circuit breakers, or full model telemetry. Those concerns are intentionally staged into later builds so the kernel contract remains small and stable.

## Standards alignment

The design follows least privilege and complete mediation principles and addresses OWASP GenAI risks around excessive agency, improper output handling, supply chain and unbounded consumption. NIST AI RMF / GenAI guidance is used as the governance basis for explicit model inventory, risk controls and lifecycle evidence.
