# Build 12 — Platform Productization

## Objective

Turn the enterprise architecture established in Builds 1–11 into a stable developer-facing platform boundary without coupling the core to a provider SDK.

## Delivered

- `platformctl` standard-library CLI package.
- Versioned machine-readable platform capability manifest.
- Explicit capability-to-boundary mapping for identity, runtime, workflow, policy, tools, models, events, evaluation, observability and resilience.
- Contract test proving manifest completeness and stability.
- Provider-neutral developer entry point that can be embedded in CI, release tooling and future SDKs.
- Enterprise repository structure with `apps/`, `packages/`, `domains/`, `infrastructure/`, `tests/`, `legacy/curriculum/`, and `docs/` ownership boundaries.
- Production platform distribution moved to `packages/platform-core` while preserving its internal package cohesion.
- Historical Months 1–6 curriculum separated under `legacy/curriculum`.
- CI, evaluation and release-attestation paths updated to the new production package location.
- ADR-0013 documenting the repository structure and migration boundary.

## Architecture

```text
fde-mastery/
├── apps/
├── packages/
│   └── platform-core/
├── domains/
├── infrastructure/
├── tests/
├── legacy/curriculum/
└── docs/
```

Within `packages/platform-core`:

```text
platform-core/
├── fde_platform/       # enterprise kernel boundaries
├── domains/            # production domain adapters
├── deployment/         # runtime/deployment infrastructure
├── persistence/        # database and migrations
├── security/           # security and AI threat controls
├── evaluation/         # evaluation and golden datasets
├── observability/      # telemetry and FinOps controls
├── custom_agents/      # tenant-specific agent framework
├── integrations/       # external integration boundaries
└── tests/              # platform-local tests
```

The platform package remains cohesive in this first structural migration. PyPA's current packaging guidance treats a `pyproject.toml` source tree as an explicit distribution boundary; `packages/platform-core` therefore owns its build metadata and runtime package instead of relying on repository-root import side effects. citeturn1search0turn1search3

## Security posture

The productization layer is an inspection/control surface, not a privileged execution bypass. Provider credentials remain outside the manifest, and future commands must preserve tenant/request context and the existing policy/tool/model gates.

The repository restructure does not weaken trust boundaries: legacy curriculum is outside the production dependency graph, and platform execution remains behind the established identity, policy, tool, model and tenant controls.

## Verification

Build 12 is complete only after the full Platform Quality workflow passes, including unit/integration tests, security controls, dependency audit, SBOM validation, staging/load smoke, production runtime smoke and Semgrep.

## Version

Platform version: **1.11.0**
