#!/usr/bin/env python3
"""Préparation : auth + liste des modèles. Pas d'Agent.create / pas de coding run.

Exit codes:
  0 OK
  3 clé absente
  4 SDK manquant
  5 modèle proposé absent
  6 AuthenticationError (clé refusée par Cursor)
  7 autre erreur SDK
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.auth_check import inspect_api_key_env  # noqa: E402
from lib.real_invoke import SMOKE_FAST_PARAM, SMOKE_MODEL_ID  # noqa: E402

AUTH_HELP = """\
Blocage auth — Cursor a refusé la clé (Invalid User API Key).
Ne pas lancer le smoke tant que ce point n'est pas vert.

Configurer :
  1. Ouvrir https://cursor.com/dashboard → Settings → API Keys
     (ou Cursor Dashboard → API Keys selon l'UI actuelle).
  2. Créer une **User API key** ou **service account key**.
     Les Team Admin keys ne sont pas supportées par le SDK.
  3. Copier la clé complète (souvent préfixe crsr_…), sans espace ni retour ligne.
  4. Dans ce shell uniquement :
       unset CURSOR_API_KEY
       export CURSOR_API_KEY='…clé…'
     (guillemets simples ; ne jamais committer ni coller la clé dans le chat)
  5. Relancer : python scripts/check_auth_and_models.py

Pièges fréquents :
  - jeton de session IDE / autre produit ≠ User API Key Cursor
  - placeholder littéral (...) laissé après l'exemple de commande
  - clé révoquée ou plan sans accès API/SDK
"""


def main() -> int:
    auth = inspect_api_key_env()
    print("auth:", auth.hint)
    if not auth.api_key_nonempty:
        return 3
    if not auth.shape_ok:
        print(
            "Refus local: forme de clé douteuse — corriger avant l'appel API.",
            file=sys.stderr,
        )
        print(AUTH_HELP, file=sys.stderr)
        return 6
    try:
        from cursor_sdk import AuthenticationError, Cursor, CursorSDKError
    except ImportError:
        print("cursor_sdk missing — run scripts/prepare_venv.sh", file=sys.stderr)
        return 4
    try:
        models = Cursor.models.list()
    except AuthenticationError as exc:
        print(f"AuthenticationError: {exc}", file=sys.stderr)
        print(AUTH_HELP, file=sys.stderr)
        return 6
    except CursorSDKError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 7
    ids = sorted({getattr(m, "id", str(m)) for m in models})
    print("models_count:", len(ids))
    print("proposed_model:", SMOKE_MODEL_ID, f"fast={SMOKE_FAST_PARAM}")
    print("proposed_available:", SMOKE_MODEL_ID in ids)
    for mid in ids[:50]:
        print("model:", mid)
    if len(ids) > 50:
        print("model: ... truncated ...")
    if SMOKE_MODEL_ID not in ids:
        print(
            "Prérequis: modèle proposé absent pour cette clé. "
            "Choisir un id listé ou vérifier le plan (SDK souvent Pro+ ; "
            "Start sans SDK d'après la doc Cursor).",
            file=sys.stderr,
        )
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
