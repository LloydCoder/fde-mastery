# FDE Mastery platform core

This directory contains the canonical production platform package. The root [README](../../README.md) is the visitor entry point; this file describes the package boundary.

## Current implementation

The repository build ledger records Builds 1–30 as completed. Build status is historical implementation and CI evidence, not proof that a customer deployment is live or certified.

See [Build Status](../../docs/BUILD-STATUS.md) and [Production Readiness](../../docs/PRODUCTION-READINESS.md).

## Install

From this directory:

```bash
python -m pip install -e ".[test,quality,security,observability,sbom]"
```

Python 3.10+ is declared in package metadata. Python 3.11 is used by the primary CI workflow.

## Test

```bash
FDE_STORAGE_BACKEND=memory FDE_RATE_LIMIT_BACKEND=memory FDE_MONTH1_PROVIDER=mock MOCK_LLM=true FDE_ENVIRONMENT=test python -m pytest -q
```

The complete Platform Quality workflow runs additional static analysis, security, migration, infrastructure, SBOM, staging and container checks.

## Main boundaries

- `fde_platform`: stable platform contracts.
- `deployment`: API gateway and deployment configuration.
- `shared_orchestrator`: agent routing and orchestration.
- `security`: trust, policy and security controls.
- `persistence`: storage adapters and migrations.
- `domains`: eight first-class domain implementations.
- `evaluation`: golden datasets, benchmarks and promotion signals.
- `integrations`: external-system contracts and adapters.
- `custom_agents`: tenant-scoped custom-agent framework.

## Related documentation

- [Architecture](../../docs/architecture/README.md)
- [API](../../docs/api/README.md)
- [Configuration](../../docs/CONFIGURATION.md)
- [Deployment](../../DEPLOYMENT.md)
- [Production readiness](../../docs/PRODUCTION-READINESS.md)
