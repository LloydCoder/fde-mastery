# FDE Mastery API Platform

## Stable surface

The public HTTP API is versioned under `/v1`. The existing gateway remains the single execution boundary; the v1 router is a compatibility facade and does not duplicate agent execution, authorization, policy, or workflow engines.

### Authentication

- API key: `X-API-Key`
- OIDC bearer token: `Authorization: Bearer <token>` when OIDC is configured
- Tenant binding for OIDC is enforced by the existing gateway identity boundary.

### Request metadata

- `X-Request-ID` may be supplied for correlation; the gateway also generates one.
- `Idempotency-Key` is required for mutating v1 calls. The legacy `X-Idempotency-Key` header remains accepted for compatibility.
- POST/PATCH retries are only safe when an idempotency key is supplied.

### Endpoints

- `GET /v1/health` — API version health probe.
- `GET /v1/capabilities` — authenticated platform capabilities.
- `POST /v1/triage/{client_id}/{domain}` — versioned facade over the existing triage execution path.

FastAPI exposes the authoritative OpenAPI 3.1 document at `/openapi.json`; SDKs should be generated or validated against that document rather than maintaining a second handwritten API schema.

## Error contract

New API contracts use RFC 9457 Problem Details semantics. The legacy gateway error object remains compatible with existing consumers during the v1 migration period.

## SDKs

- `sdks/python` — dependency-free Python client using the standard library.
- `sdks/typescript` — Fetch-based TypeScript client for Node 20+ and compatible runtimes.

Both clients enforce HTTPS outside localhost, require idempotency keys for mutations, propagate request IDs, and only retry transient responses when retrying is safe.
