# `fde_platform` — platform kernel

This is the framework-neutral kernel for the active FDE Mastery platform.

## Responsibilities

- stable cross-boundary contracts
- ports for agent, model, tool, repository and event-bus capabilities
- immutable identity/request context primitives
- first-class agent execution lifecycle and runtime safety boundaries
- executable dependency-boundary metadata

## Runtime boundary

`fde_platform.runtime` owns `AgentRun` lifecycle, execution budgets, cooperative cancellation, checkpoints, and the `RunStore` persistence port. It deliberately does not own workflow scheduling, model-provider calls, tool execution, or infrastructure concerns.

```text
Application / API / Worker
            ↓
     AgentRuntime
            ↓
     AgentRun + Context
            ↓
       Domain Agent
            ↓
       RunStore port
```

Build 3 keeps the reference runtime synchronous. Durable persistence, queue-backed workers, replay, and workflow recovery are deferred to Build 4.

## Non-responsibilities

The kernel must not import or instantiate:

- FastAPI or other web frameworks
- PostgreSQL/SQLAlchemy drivers
- model-provider SDKs
- concrete infrastructure adapters
- domain implementations
- legacy Month 1–6 curriculum modules

Concrete implementations belong outside the kernel and are introduced behind these contracts in later builds.
