# ADR 0001 — Month 7 Platform Architecture

## Status

Accepted

## Decision

Month 7 uses a layered architecture:

1. FastAPI gateway
2. Authentication and authorization
3. Request controls
4. Central `AgentRouter`
5. Domain adapters implementing `DomainAgent`
6. Repository abstraction for durable state
7. Observable structured responses

Persistence is selected through configuration. In-memory storage is the default for deterministic local tests; PostgreSQL is the durable deployment backend. Redis is an optional distributed rate-limit backend.

## Rationale

The platform must demonstrate both FDE practicality and production engineering discipline. Domain agents should remain independently testable while the platform owns cross-cutting concerns such as identity, tenant isolation, rate limiting, persistence, observability, and evaluation.

## Consequences

- Domain agents are decoupled from API and storage implementation.
- Local demos remain easy to run.
- Production deployments can use durable/distributed infrastructure.
- More interfaces and configuration are introduced, increasing operational complexity.
