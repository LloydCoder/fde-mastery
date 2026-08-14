#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts
cyclonedx-py environment --output-format json --output-file artifacts/sbom.cdx.json
