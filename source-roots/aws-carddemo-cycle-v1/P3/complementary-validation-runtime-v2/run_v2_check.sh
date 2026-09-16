#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$ROOT/tools/enrich_and_check.py" \
  --runtime-v1 "$ROOT/../complementary-validation-runtime-v1" \
  --checker "$ROOT/../complementary-validation-implementation-v3" \
  --out-root "$ROOT/evidence"
