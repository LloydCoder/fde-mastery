# ADR 0022 — Commercial Entitlements Plane

## Status

Accepted

## Decision

Introduce a provider-neutral commercial contract for versioned product plans, tenant subscriptions, feature entitlements and idempotent usage metering.

## Boundaries

The commercial plane does not process payments, store payment credentials, calculate tax, issue invoices or replace authorization. External billing providers remain responsible for payment collection and invoicing. Existing identity, authorization, observability and persistence boundaries remain authoritative.

## Security

- Every subscription and usage event is tenant-bound.
- Entitlement checks fail closed when subscription or plan state is unavailable.
- Idempotency keys are scoped to tenant identity.
- Reuse of an idempotency key with different event semantics is rejected.
- Usage quantities must be finite and positive.
- Metadata is bounded to control cardinality and data exposure.
- No secrets or payment credentials are accepted by the contracts.

## Compatibility

Plan versions are immutable. A subscription references an explicit plan version so a pricing change does not silently mutate an existing entitlement contract.

## Rationale

SaaS platforms benefit from a shared tenant control plane and explicit isolation. Current billing systems also separate entitlement decisions from usage metering and payment processing. Keeping these concerns separate avoids coupling the FDE kernel to a payment provider and prevents a second authorization or telemetry system from emerging.
