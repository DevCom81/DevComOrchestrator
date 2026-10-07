#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$ROOT/scripts/check_size_limits.py"
node "$ROOT/scripts/check_size_limits_ts.mjs"
