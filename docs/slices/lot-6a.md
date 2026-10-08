# LOT 6A — Spike liaison Cursor (preuve)

## Statut

Préparation verte (doubles). Smoke réel : **à lancer par Jérôme** après
`COST_SMOKE.md` + clé API + GO. Agent DevCom : **aucune** invocation payante.

## Objectif

Prouver : paquet → invoke Cursor → modification obtenue → capture (suivis,
indexés, nouveaux) → retour rattaché → validation locale (commande, exit, logs).

## Prérequis bloquants (ne pas contourner)

1. **`CURSOR_API_KEY`** User/service-account valide (Dashboard → API Keys).
   Absente = exit 3 ; refusée (`Invalid User API Key`) = exit **6**.
2. Plan avec **SDK** (doc : Start **sans** SDK → Pro+).
3. `check_auth_and_models.py` → exit 0 et `proposed_available: True`.
4. Spending consulté ; on-demand OFF recommandé (seul frein € compte).
5. `ALLOW_CURSOR_SMOKE=1` après lecture fiche coût.

Ne pas contourner un exit 6 : régénérer la clé, `unset` puis `export` propre.

## Modèle / coût

Voir `spikes/cursor_lot6a/COST_SMOKE.md` : `composer-2.5` + `fast=false` ;
**aucun plafond € garanti par le script** ; timeout ≠ garantie financière.

## Commandes manuelles

### A — Préparation (sans Agent.create coding)

```bash
cd /home/jey/Projets/MyProjects/DevComOrchestrator/spikes/cursor_lot6a
source .venv/bin/activate
./scripts/init_fixture_git.sh
export PYTHONPATH=.
pytest -q tests
python scripts/simulate_spike_doubles.py
python scripts/smoke_real_guard.py ; echo exit=$?
# Attendu : tests verts ; SPIKE_DOUBLES_OK ; garde exit=2

# Auth + modèles (API métadonnées ; pas de coding agent)
# export CURSOR_API_KEY=...   # shell local, jamais commit
python scripts/check_auth_and_models.py
# Attendu : auth OK ; proposed_available: True
```

### B — Run payant (Jérôme seulement)

```bash
cd /home/jey/Projets/MyProjects/DevComOrchestrator/spikes/cursor_lot6a
source .venv/bin/activate
export PYTHONPATH=.
# Relire COST_SMOKE.md ; cocher la décision
export CURSOR_API_KEY=...          # si pas déjà dans le shell
export ALLOW_CURSOR_SMOKE=1
python scripts/smoke_real_guard.py # exit 0
python scripts/run_real_smoke.py   # UN send, zéro retry
# Attendu : SMOKE_REAL_OK ; artefacts sous artifacts/smoke-1/
# En cas d'échec auth/sandbox/budget : noter le message ; ne pas forcer.
```

## Exclusions

LOT 6B, MAIL, push, projets quotidiens, retry auto.
