#!/usr/bin/env bash
# Prépare le venv spike (pas le .venv backend). Aucun run Cursor.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -c "import cursor_sdk; print('cursor_sdk OK', getattr(cursor_sdk, '__version__', 'unknown'))"
echo "Venv prêt : $ROOT/.venv"
