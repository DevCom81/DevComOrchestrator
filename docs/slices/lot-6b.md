# LOT 6B — Adapter Cursor intégré

## Statut

Implémenté — validation manuelle (doubles) ; smoke UI réel lancé par Jérôme.

## Objectif

Parcours HQ : plan → GO execute → Cursor → retour auto → revue → corrections
bornées → intégration branche locale (GO) ; manuel = dépannage.

## Critères

- [ ] GO execute distinct (paquet, base Git propre, modèle, permissions, budget)
- [ ] Chaque send = nouveau GO ; corrections ≤ 2 / version (persistées)
- [ ] Intention avant invoke ; start idempotent ; pas de double send
- [ ] Cancel demandé ≠ confirmé ; capture si écritures stables
- [ ] Retour auto rattaché ; revue sans fichiers manuels
- [ ] Intégration worktree + branche + commit local ; hint cherry-pick
- [ ] Fake explicite démo ; réel sans clé = blocage clair
- [ ] `.env` / `.env.example` / `devcom_start.sh`
- [ ] Tests doubles verts ; zéro appel payant agent

## Exclusions

LOT 7, spike 6A, push/merge implicites, retry auto.

## Smoke produit (Jérôme)

Après doubles verts : démarrer démo Fake, puis éventuellement un run réel UI
unique avec clé — hors agent.

## Commandes de validation (manuel)

```bash
cd backend
source .venv/bin/activate
export PYTHONPATH=src
alembic upgrade head
ruff check src tests && mypy src
pytest -q tests/integration/test_cursor_lot6.py \
  tests/integration/test_cursor_lot6b.py \
  tests/integration/test_cursor_lot6b_integrate.py \
  tests/integration/test_tech_api_flow.py \
  tests/integration/test_tech_durability.py
cd ../frontend && npm run lint && npm run test -- --run && npm run build
# Depuis la racine (après build) :
#   ./scripts/devcom_start.sh demo
# Smoke réel UI (optionnel, 1 run) : ./scripts/devcom_start.sh real — lancé par Jérôme
```
