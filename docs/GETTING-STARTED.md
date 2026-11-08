# Getting started

This guide runs FDE Mastery locally using in-memory storage and mock-provider settings. It does not provision cloud resources or connect to customer systems.

## Prerequisites

- Git
- Python 3.10 or newer; Python 3.11 matches the primary CI runtime
- A supported shell (Bash examples below)

## Clone and install

```bash
git clone https://github.com/LloydCoder/fde-mastery.git
cd fde-mastery/packages/platform-core
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test,quality]"
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Run the test suite

```bash
FDE_STORAGE_BACKEND=memory FDE_RATE_LIMIT_BACKEND=memory FDE_MONTH1_PROVIDER=mock MOCK_LLM=true FDE_ENVIRONMENT=test python -m pytest -q
```

The complete Platform Quality workflow includes additional security, migration, static-analysis, infrastructure, SBOM, staging and Docker checks. See [CI Verification Contract](CI-VERIFICATION-CONTRACT.md).

## Inspect the platform manifest

From the repository root:

```bash
PYTHONPATH=packages/platform-core python -m platformctl manifest
PYTHONPATH=packages/platform-core python -m platformctl doctor
```

## Start the local API

After installing the package, from `packages/platform-core`:

```bash
FDE_STORAGE_BACKEND=memory FDE_RATE_LIMIT_BACKEND=memory FDE_MONTH1_PROVIDER=mock MOCK_LLM=true FDE_ENVIRONMENT=test python -m uvicorn deployment.api_gateway.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
curl --fail http://127.0.0.1:8000/v1/health
```

See [API reference](api/README.md) for authentication, tenant binding, idempotency and request metadata.

## Next steps

- Review [architecture](architecture/README.md).
- Read [configuration](CONFIGURATION.md).
- Review [production readiness](PRODUCTION-READINESS.md) before connecting external systems.
- Follow [CONTRIBUTING.md](../CONTRIBUTING.md) before submitting changes.
