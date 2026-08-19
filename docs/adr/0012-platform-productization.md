# ADR-0012 — Platform Productization Boundary

- **Status:** Accepted
- **Date:** 2026-08-19
- **Decision:** Provide a dependency-light developer control surface over the enterprise platform without moving provider-specific execution into the CLI.

## Context

Builds 1–11 established the platform kernel, identity, runtime, workflows, policy, tool/model gateways, events, evaluation, observability and enterprise recovery controls. The platform now needs a stable developer-facing surface that can be used by CI, release automation and future SDKs.

## Decision

Introduce `platformctl` as a provider-neutral inspection boundary with a versioned capability manifest. The manifest describes platform capabilities and their architectural boundaries but contains no credentials, tenant secrets, provider configuration or privileged execution bypasses.

The CLI remains intentionally dependency-light and delegates actual execution to the established platform boundaries. Future commands MUST preserve request context, tenant isolation, policy enforcement and tool/model gates.

## Consequences

- Developers get a stable entry point without coupling the kernel to provider SDKs.
- CI can inspect capabilities deterministically.
- The manifest becomes an explicit compatibility surface for future SDKs.
- Privileged operations remain behind the existing trust boundaries.
- The repository can evolve toward a package/SDK layout without another architectural rewrite.

## Security requirements

- No secret material in the manifest.
- No direct provider calls from `platformctl`.
- No authorization bypass.
- No cross-tenant context construction.
- Capability changes require contract-test coverage.
