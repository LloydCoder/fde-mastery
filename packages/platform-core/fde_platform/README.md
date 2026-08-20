# `fde_platform` — enterprise platform kernel

This package is the framework-neutral kernel for the active FDE Mastery platform. It is organized as a modular monolith with explicit control-plane, data-plane and trust-plane boundaries so components can be extracted into independently deployed services later without changing domain contracts.

## Core responsibilities

- stable cross-boundary contracts and ports
- immutable identity, tenant and request context
- agent execution lifecycle, budgets, checkpoints and cancellation
- durable workflow state and queue contracts
- versioned agent/tool/model/policy registries
- independent policy enforcement and risk-tier controls
- human approval lifecycle with quorum and expiry
- model and tool integration boundaries
- event/outbox contracts
- AI decision lineage, FinOps and incident lifecycle
- MCP/A2A interoperability contracts with explicit authorization references
- workload sandbox policy for untrusted/custom execution
- observability-safe operational boundaries

## Architecture boundary

```text
                    CONTROL PLANE
 identity · tenants · registries · policies · evaluations · deployments
                              │
                              ▼
API / Gateway → Authorization → Policy Decision → Durable Workflow
                                              │
                                              ▼
                                        Agent Runtime
                                          /        \
                                         /          \
                                Model Gateway     Tool Gateway
                                     │                │
                               Providers        Enterprise Systems
                                         \          /
                                          ▼        ▼
                                      Event / Audit
                                           │
                              Evaluation · FinOps · Incidents
                                           │
                                      Observability

                    TRUST PLANE
        identity · least privilege · approvals · sandbox · audit
```

## Security invariant

The model is never the authorization authority. LLM output is treated as an untrusted proposal. High-impact actions are evaluated by the independent trust-plane policy boundary and may require explicit human approval before execution.

## Interoperability

`fde_platform.protocols` defines narrow MCP and A2A contracts. These are protocol boundaries, not security boundaries. Every external tool or agent message must carry an authorization reference and remain subject to tenant, policy and risk enforcement.

## Deployment model

`fde_platform.deployment` defines shared, isolated and dedicated customer deployment profiles. The current repository remains a modular monolith by design; service extraction is reserved for workloads that require independent scaling, isolation or regional residency.

## Non-responsibilities

The kernel must not import or instantiate:

- FastAPI or other web frameworks
- PostgreSQL/SQLAlchemy drivers
- model-provider SDKs
- concrete infrastructure adapters
- domain implementations
- legacy Month 1–6 curriculum modules

Concrete implementations remain outside the kernel and are introduced behind ports/contracts. The kernel therefore remains testable without external credentials or live customer systems.
