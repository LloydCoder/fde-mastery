# Build 21 — API Platform & SDKs

## Objective

Turn the existing FastAPI gateway into a stable, versioned, contract-driven public API surface and provide maintained Python and TypeScript SDKs without duplicating execution, policy, authorization or workflow engines.

## Research basis

The implementation was reviewed against current OpenAPI, FastAPI, RFC 9457 and OWASP API-security guidance. OpenAPI is the language-neutral API description standard; FastAPI currently emits OpenAPI 3.1; RFC 9457 defines machine-readable HTTP Problem Details; and current IETF HTTPAPI work treats idempotency keys as a mechanism for making non-idempotent requests fault-tolerant. citeturn0search2turn1search2turn0search0turn0search4

## Delivered

- Stable `/v1` API facade.
- Versioned health, capabilities and triage endpoints.
- Existing gateway remains the single execution path.
- Existing API-key/OIDC authentication remains authoritative.
- Standard `Idempotency-Key` support while retaining legacy `X-Idempotency-Key` compatibility.
- RFC 9457 Problem Details for v1 execution errors.
- Request correlation via `X-Request-ID`.
- Public API contract package for idempotency, request metadata, pagination and problem details.
- Python SDK with HTTPS enforcement, auth selection, request correlation, bounded retries and safe mutation retry rules.
- TypeScript Fetch SDK with the same safety properties.
- Dedicated TypeScript SDK typecheck workflow.
- API/SDK ADR and documentation.

## Security

- HTTPS is required by SDKs outside localhost.
- Credentials never enter URLs.
- Mutating requests require idempotency keys.
- POST/PATCH retries are disabled unless idempotency is explicit.
- Retryable HTTP responses are limited to 429/502/503/504 and respect numeric `Retry-After`.
- Server-side tenant and scope authorization remains in the existing gateway.
- v1 does not create a second authorization or execution engine.

## Verification

Build 21 is GREEN only after Platform Quality, Semgrep and the dedicated SDK Quality workflow pass.
