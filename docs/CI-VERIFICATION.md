# CI Verification Contract

## Purpose

This repository treats GitHub Actions as a release gate. A change is not considered verified until the required Platform Quality workflow has completed successfully for the exact commit being considered for merge.

## Required workflow events

`Platform Quality` runs on:

- pushes to `main`
- pull requests
- merge queue (`merge_group`)
- manual dispatch

The merge-queue trigger is intentional: GitHub requires workflows used as required checks to run for the `merge_group` event when a repository uses a merge queue.

## Required evidence

The final merge candidate must have successful results for:

- Test, Security and Build
- Static security scan / Semgrep
- tests and domain adapter verification
- enterprise deployment/security gates
- migration validation
- Ruff, MyPy and Bandit
- dependency audit
- compile validation
- Terraform validation
- SBOM generation and validation
- staging API and load smoke
- production Docker/runtime smoke

A previous successful run for an earlier SHA does not satisfy this contract.

## Security posture

Workflows use least-privilege `contents: read` permissions and do not use `pull_request_target` to execute untrusted pull-request code. Production deployment and provenance workflows remain separate from test execution.
