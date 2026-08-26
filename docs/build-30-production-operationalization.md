# Build 30 — Production Operationalization

## Objective

Convert the existing enterprise platform contracts into an explicit, machine-checkable operational readiness boundary without introducing another parallel control plane.

## Scope

- deterministic production configuration validation;
- fail-closed readiness reporting;
- persistent PostgreSQL requirement in production;
- distributed Redis rate-limit requirement in production;
- managed-secrets requirement in production;
- OIDC issuer/audience requirement in production;
- production prohibition of mock model execution;
- canonical domain-router verification;
- machine-readable `/ready` response;
- regression coverage for every readiness invariant.

## Design boundary

`/health` remains a liveness signal and must not require external dependency success. `/ready` reports whether the application satisfies the configuration and platform invariants required to enter production. Remote dependency health checks remain deployment-specific and must not be conflated with static configuration readiness.

No plaintext secret material is introduced. No custom vault/KMS is introduced. The existing provider-neutral persistence and secrets boundaries remain authoritative.

## Acceptance criteria

- [x] Production readiness is evaluated from the validated `Settings` contract.
- [x] Production cannot report ready with in-memory storage.
- [x] Production cannot report ready with in-process rate limiting.
- [x] Production cannot report ready with environment-backed secrets.
- [x] Production cannot report ready without OIDC issuer and audience.
- [x] Production cannot report ready with mock LLM execution enabled.
- [x] Production cannot report ready when the domain router differs from the canonical domain contract.
- [x] Readiness returns structured check results for operators.
- [x] Regression tests cover the fail-closed boundaries.

## Next slices

1. Exercise real PostgreSQL and Redis health in the deployment environment.
2. Bind the managed secrets provider through the existing Build 29 provider boundary.
3. Add deployment-level readiness probes and evidence collection.
4. Execute the Tinlance → FDE Mastery production contract against a real staging environment.
5. Add rollback/recovery evidence before declaring the complete production-readiness program GREEN.
