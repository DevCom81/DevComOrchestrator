#!/usr/bin/env bash
# Initialise le dépôt fixture local (sans remote, sans données perso).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIX="$ROOT/fixture"
cd "$FIX"
if [[ -d .git ]]; then
  echo "fixture/.git déjà présent"
  exit 0
fi
git init -b main
git add hello.py test_hello.py PACKAGE.md
git -c user.email="spike@devcom.local" -c user.name="Spike Fixture" commit -m "spike fixture baseline"
echo "Fixture git prêt : $FIX"
