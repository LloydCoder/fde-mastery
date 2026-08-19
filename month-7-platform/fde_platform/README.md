# `fde_platform` — platform kernel

This is the framework-neutral kernel for the active FDE Mastery platform.

## Responsibilities

- stable cross-boundary contracts
- ports for agent, model, tool, repository and event-bus capabilities
- executable dependency-boundary metadata

## Non-responsibilities

The kernel must not import or instantiate:

- FastAPI or other web frameworks
- PostgreSQL/SQLAlchemy drivers
- model-provider SDKs
- concrete infrastructure adapters
- domain implementations
- legacy Month 1–6 curriculum modules

Concrete implementations belong outside the kernel and are introduced behind these contracts in later builds.
