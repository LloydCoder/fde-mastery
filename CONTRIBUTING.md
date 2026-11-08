# Contributing to FDE Mastery

Thank you for considering a contribution. Changes should preserve the platform's identity, tenant, policy, workflow, tool/model and audit boundaries.

## Before opening an issue

- Search existing issues and documentation.
- For defects, include reproducible steps, expected and actual behavior, and sanitized logs.
- For security vulnerabilities, follow [SECURITY.md](./SECURITY.md). Do not open a public issue containing exploit details.
- Never include customer data, credentials, tokens or private keys.

## Development setup

Use Python 3.11 to match primary CI (the package supports Python 3.10+).

```bash
git clone https://github.com/LloydCoder/fde-mastery.git
cd fde-mastery/packages/platform-core
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test,quality,security,redis,observability,sbom]"
```

For a local test run:

```bash
FDE_STORAGE_BACKEND=memory FDE_RATE_LIMIT_BACKEND=memory FDE_MONTH1_PROVIDER=mock MOCK_LLM=true FDE_ENVIRONMENT=test python -m pytest -q
```

Run focused tests while iterating, then run the complete repository workflow before requesting review. The authoritative commands are in [Platform Quality](./.github/workflows/platform-tests.yml) and [SDK Quality](./.github/workflows/sdk-quality.yml).

## Contribution workflow

1. Fork the repository.
2. Create a focused branch from `main`, such as `fix/tenant-scope-check` or `docs/api-guide`.
3. Make the smallest complete change that addresses the issue.
4. Add or update tests for behavior changes.
5. Update documentation and operational guidance when contracts change.
6. Run relevant tests, linters and security checks.
7. Push your branch and open a pull request against `main`.
8. Address review feedback and ensure required checks pass before merge.

## Engineering expectations

- Preserve server-side authorization and tenant isolation. Client-side filtering is not an access-control boundary.
- Treat model output, prompts, tool results, webhooks and external API responses as untrusted input.
- Model output must never become an authorization decision.
- Require explicit policy and human approval for high-impact actions.
- Preserve request correlation, idempotency and auditable decision evidence.
- Do not place secrets, customer data or production exports in Git.
- Prefer typed contracts, deterministic behavior and explicit failure handling.
- Do not claim customer-production readiness based only on unit tests or a green workflow.
- Preserve modular-monolith boundaries unless a documented architecture decision justifies a change.

## Tests and quality checks

At minimum, run tests relevant to the changed package. For platform changes, use the complete Platform Quality workflow. For TypeScript SDK changes:

```bash
cd sdks/typescript
npm install --no-save --no-package-lock typescript@5.9.3
npx tsc --noEmit -p tsconfig.json
```

Do not weaken or remove a security check solely to make a workflow pass. Explain unavoidable limitations in the pull request.

## Commit messages

Use Conventional Commit-style messages consistent with repository history:

- `feat: add tenant-scoped connector health`
- `fix: reject expired approval grants`
- `docs: clarify local API setup`
- `test: cover workflow replay boundary`

## Pull request checklist

- [ ] The change has a clear problem statement and bounded scope.
- [ ] Tests cover new or changed behavior.
- [ ] Tenant, authorization and policy boundaries are preserved.
- [ ] No secrets or customer-sensitive data are included.
- [ ] Documentation and configuration examples are updated.
- [ ] Relevant CI and security checks pass.
- [ ] Operational or migration impact is described.

By submitting a contribution, you agree that your contribution is provided under the repository's Apache-2.0 license, subject to applicable law and the license terms.
