# Build 25 — Commercial Entitlements & Usage Plane

## Objective

Add a provider-neutral commercial boundary that connects a tenant to a versioned product plan, feature entitlements and auditable usage metering without duplicating payments, invoicing, telemetry or authorization engines.

## Research basis

Current SaaS billing platforms separate product entitlements from payment collection and use explicit usage meters for usage-based pricing. Stripe documents entitlements as feature access mapped to subscription state and usage billing as an ingestion → catalog → billing → monitoring lifecycle. OpenMeter similarly separates high-volume usage data from transactional billing state and emphasizes deduplication and tenant/customer attribution. AWS SaaS guidance treats tenant isolation as a separate concern from authentication/authorization and requires explicit tenant-scoped resource boundaries.

## Delivered

- Versioned plans and immutable plan versions.
- Tenant-bound subscriptions with explicit lifecycle states.
- Feature entitlements with optional finite limits and units.
- Fail-closed entitlement decisions.
- Subscription-to-known-plan validation.
- Tenant isolation in access decisions.
- Tenant + idempotency-key usage deduplication.
- Protection against semantic idempotency-key reuse.
- Decimal, finite, positive usage quantities.
- Bounded metadata/cardinality controls.
- Python 3.10-compatible standard-library implementation.
- Provider-neutral boundary: no payment credentials, tax logic, card data or invoice generation.
- Reuse of existing identity/authorization, observability and persistence boundaries.

## Security model

The commercial plane is not an authorization replacement. It answers product-entitlement questions only. Server-side identity and authorization remain authoritative. A missing subscription, unavailable plan or inactive subscription fails closed.

Usage keys are tenant-scoped so an idempotency key from one tenant cannot suppress usage belonging to another tenant. Reusing a key with different event semantics is rejected rather than silently merged.

Metadata is bounded to reduce unbounded-cardinality and data-exfiltration risk. No raw customer content or credentials are accepted by the contracts.

## Non-goals

- No payment processing.
- No storage of card/payment credentials.
- No tax calculation.
- No invoice issuance.
- No replacement for `observability/billing_meter.py` as an unmodified legacy compatibility surface in this build; migration should be explicit and separately verified.
- No replacement for the platform authorization engine.
- No autonomous commercial commitments or spend approvals.

## Verification

Build-specific tests cover:

- tenant isolation;
- plan-version integrity;
- subscription lifecycle fail-closed behavior;
- entitlement decisions;
- usage idempotency;
- semantic idempotency-key reuse;
- cross-tenant usage isolation;
- finite numeric validation;
- bounded metadata.

The repository-wide CI pipeline remains the merge gate for security, static analysis, migrations, SBOM, staging/load and production runtime validation.
