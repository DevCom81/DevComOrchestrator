#!/usr/bin/env bash
# Clone le fixture dans un worktree isolé (pas les projets quotidiens).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_ID="${1:-smoke-1}"
SRC="$ROOT/fixture"
DEST="$ROOT/worktrees/$RUN_ID"
if [[ ! -d "$SRC/.git" ]]; then
  echo "Exécuter d'abord scripts/init_fixture_git.sh" >&2
  exit 1
fi
rm -rf "$DEST"
mkdir -p "$ROOT/worktrees"
git clone --local "$SRC" "$DEST"
echo "Worktree : $DEST"
