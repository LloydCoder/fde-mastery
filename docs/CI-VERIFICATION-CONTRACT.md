# CI Verification Contract

The repository treats GitHub Actions as a release gate. A change is not considered verified until the required Platform Quality workflow has completed successfully for the exact commit being considered for merge.

## Required workflow events

`Platform Quality` runs on:

- pushes to `main` and build branches
- pull requests
- merge queue (`merge_group`)
- manual dispatch

The merge-queue trigger is required when the repository uses a merge queue.

## Required evidence

A merge candidate must have successful results for:

- test, security and build
- static security scan / Semgrep
- all eight first-class domain adapter verification
- enterprise deployment/security gates
- migration validation
- Ruff, MyPy and Bandit
- dependency audit
- compile and CLI validation
- Terraform validation
- SBOM generation and validation
- staging API and load smoke
- production Docker/runtime smoke

A previous successful run for an earlier SHA does not satisfy this contract.

## Domain contract

The canonical first-class domain set is exactly:

1. cybersecurity
2. finance
3. healthtech
4. logistics
5. legal
6. revops
7. procurement
8. custom

CI must fail if this set drifts unexpectedly.

## Security posture

Workflows use least-privilege `contents: read` permissions and do not use `pull_request_target` to execute untrusted pull-request code. Production deployment and provenance workflows remain separate from test execution.
