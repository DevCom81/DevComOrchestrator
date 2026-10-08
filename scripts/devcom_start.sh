#!/usr/bin/env bash
# Lancement quotidien DevCom — une commande, choix démo/réel.
# Pas d'install/build automatique. Aucun appel payant au démarrage.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-}"
if [[ "$MODE" != "demo" && "$MODE" != "real" ]]; then
  echo "Usage: $0 demo|real" >&2
  echo "Démo: Fake LLM + Fake Cursor. Réel: exige .env (clés) et adapters real." >&2
  exit 2
fi
BACKEND="$ROOT/backend"
DIST="$ROOT/frontend/dist"
ENV_FILE="$BACKEND/.env"
if [[ ! -d "$BACKEND/.venv" ]]; then
  echo "Prérequis manquant: backend/.venv"
  echo "Commande: cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev,openai]'"
  exit 1
fi
# shellcheck disable=SC1091
source "$BACKEND/.venv/bin/activate"
if [[ ! -d "$DIST" ]]; then
  echo "Prérequis manquant: frontend/dist (frontend compilé)"
  echo "Commande: cd frontend && npm ci && npm run build"
  exit 1
fi
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Prérequis manquant: backend/.env"
  echo "Commande: cp backend/.env.example backend/.env && chmod 600 backend/.env"
  exit 1
fi
export DEVCOM_MODE="$MODE"
if [[ "$MODE" == "demo" ]]; then
  export DEVCOM_LLM_ADAPTER="${DEVCOM_LLM_ADAPTER:-fake}"
  export DEVCOM_CURSOR_ADAPTER="${DEVCOM_CURSOR_ADAPTER:-fake}"
else
  export DEVCOM_LLM_ADAPTER="${DEVCOM_LLM_ADAPTER:-openai}"
  export DEVCOM_CURSOR_ADAPTER="${DEVCOM_CURSOR_ADAPTER:-real}"
fi
export DEVCOM_FRONTEND_DIST="$DIST"
cd "$BACKEND"
export PYTHONPATH=src
if ! alembic current >/dev/null 2>&1; then
  echo "Prérequis manquant: migrations Alembic (schéma SQLite)"
  echo "Commande: cd backend && source .venv/bin/activate && export PYTHONPATH=src && alembic upgrade head"
  exit 1
fi
HEAD="$(alembic heads 2>/dev/null | awk '{print $1}' | head -1)"
CUR="$(alembic current 2>/dev/null | awk '{print $1}' | head -1)"
if [[ -z "$CUR" || "$CUR" != "$HEAD" ]]; then
  echo "Prérequis manquant: schéma pas à jour (current=${CUR:-none} head=${HEAD:-unknown})"
  echo "Commande: cd backend && source .venv/bin/activate && export PYTHONPATH=src && alembic upgrade head"
  exit 1
fi
echo "DevCom $MODE — http://127.0.0.1:${DEVCOM_PORT:-8765} (dist servi par le backend)"
echo "Dev Vite: cd frontend && npm run dev (séparé)"
exec uvicorn devcom.bootstrap.app_factory:create_app --factory \
  --host "${DEVCOM_HOST:-127.0.0.1}" --port "${DEVCOM_PORT:-8765}"
