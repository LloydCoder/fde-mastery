#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-artifacts}"
mkdir -p "$OUT_DIR"
python -m pip install --disable-pip-version-check "cyclonedx-bom>=7.0"
cyclonedx-py environment --of JSON --output-version 1.6 --output-file "$OUT_DIR/sbom.cdx.json"
printf 'SBOM written to %s\n' "$OUT_DIR/sbom.cdx.json"
