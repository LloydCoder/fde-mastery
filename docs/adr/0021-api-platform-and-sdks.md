# ADR 0021 — API Platform & SDKs

## Decision

Expose a stable `/v1` HTTP surface through the existing FastAPI gateway and treat the gateway's generated OpenAPI 3.1 document as the API contract. Provide maintained Python and TypeScript clients over that contract.

## Boundaries

The v1 facade MUST NOT create a second execution or authorization engine. Authentication remains delegated to the existing API-key/OIDC boundary. Tenant authorization remains enforced server-side.

## Reliability

Mutating calls use `Idempotency-Key`. Automatic retries are limited to transient HTTP failures and are only permitted for mutations when an idempotency key exists. `Retry-After` is honored when numeric.

## Security

- HTTPS is required outside localhost for SDKs.
- Credentials are never placed in URLs.
- Client IDs and domains are path-encoded by the TypeScript SDK.
- Server-side tenant checks remain authoritative.
- API errors must not expose stack traces or internal secrets.

## Interoperability

OpenAPI is the language-neutral contract. This allows standards-based SDK generation and contract testing rather than maintaining separate handwritten wire specifications.
