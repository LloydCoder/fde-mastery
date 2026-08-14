# API Reference

The platform exposes domain execution behind the router. Every request must be authenticated and authorized for the target tenant.

## Execution contract

`POST /api/{tenant_id}/agents/{domain}`

Domains: `cybersecurity`, `finance`, `healthtech`, `logistics`, `legal`, `revops`.

Required headers:

- `Authorization: Bearer <OIDC access token>`
- `X-Request-ID: <uuid>` (optional; generated when absent)

The token must contain `sub`, `iss`, `aud`, `exp`, `iat`, `tenant_id`, and the required scope.

## Errors

- `401` authentication failure
- `403` authorization or tenant isolation failure
- `422` invalid request
- `429` rate limit
- `503` circuit open / dependency unavailable
- `504` agent timeout

Never return provider credentials, raw exception traces, prompts containing secrets, or another tenant's data.
