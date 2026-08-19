# ADR 0008 — Event-Driven Platform Backbone

- **Status:** Accepted
- **Date:** 2026-08-19
- **Build:** 8

## Context

Agent and workflow execution increasingly needs asynchronous fan-out, durable publication, independent consumers, retries and replayable facts. Direct database-plus-broker dual writes create a failure window in which state and notification diverge.

## Decision

FDE Mastery will use a framework-neutral event contract and a transactional outbox/inbox architecture.

1. Every event has an immutable ID, explicit type, schema version, source, tenant/environment context, subject and correlation/causation metadata.
2. Domain state and publication intent are committed in one database transaction through the outbox.
3. A publisher claims outbox rows with leases and publishes them at least once.
4. Consumers deduplicate with a consumer-scoped inbox key `(consumer_name, event_id)`.
5. Delivery failures use bounded retries and a terminal dead-letter state.
6. Ordering is explicit per partition/aggregate key; global ordering is not promised.
7. Event payloads are schema-versioned and opaque to the platform kernel.
8. Tenant isolation is enforced at the database boundary with FORCE RLS as well as application context.
9. Event replay is a separate operational concern; consumers must be deterministic and idempotent.

## Consequences

### Positive

- Eliminates the database/broker dual-write consistency gap.
- Supports horizontal publishers and consumers.
- Makes duplicate delivery a defined, testable property.
- Provides durable operational evidence for failed publication.
- Preserves domain ownership of event schemas.

### Trade-offs

- At-least-once delivery requires idempotent consumers.
- Outbox retention and replay storage require lifecycle management.
- Cross-service workflows remain eventually consistent and may require sagas.
- Per-partition ordering is more scalable than global ordering but requires explicit keys.

## Standards and research basis

The design follows the transactional outbox pattern documented by AWS Prescriptive Guidance: persist the business change and event intent atomically, then publish asynchronously; consumers must tolerate duplicates. It also follows CloudEvents-inspired envelope semantics without coupling the core to a broker or SDK.
