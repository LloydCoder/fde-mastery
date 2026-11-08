# FDE Mastery documentation

This directory contains architecture explanations, decision records, build evidence and operational guidance. The canonical implementation is under `packages/platform-core`; historical curriculum material is under `legacy/curriculum`.

## Recommended reading paths

### New contributors

1. [Getting started](GETTING-STARTED.md)
2. [Repository architecture](architecture/README.md)
3. [API and SDK contracts](api/README.md)
4. [Configuration](CONFIGURATION.md)
5. [Contributing](../CONTRIBUTING.md)

### Platform architects

1. [Architecture guide](architecture/README.md)
2. [Architecture decision records](adr/)
3. [Enterprise security standards map](SECURITY-STANDARDS-MAP.md)
4. [Build status ledger](BUILD-STATUS.md)

### Operators and deployment teams

1. [Deployment guide](../DEPLOYMENT.md)
2. [Configuration reference](CONFIGURATION.md)
3. [Production readiness gates](PRODUCTION-READINESS.md)
4. [CI verification contract](CI-VERIFICATION-CONTRACT.md)
5. [Security standards map](SECURITY-STANDARDS-MAP.md)

## Documentation by Diátaxis purpose

| Purpose | Material |
|---|---|
| Tutorials | [Getting started](GETTING-STARTED.md); historical exercises in [legacy/curriculum](../legacy/curriculum/) |
| How-to guides | [Deployment](../DEPLOYMENT.md), [configuration](CONFIGURATION.md), [production readiness](PRODUCTION-READINESS.md) |
| Explanation | [Architecture](architecture/README.md), [ADRs](adr/), [security standards](SECURITY-STANDARDS-MAP.md) |
| Reference | [API](api/README.md), [build status](BUILD-STATUS.md), [CI verification contract](CI-VERIFICATION-CONTRACT.md) |

Build records are historical engineering evidence. Consult current workflow runs and the deployment environment before making claims about present operational status.
