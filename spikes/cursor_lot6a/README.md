# Spike LOT 6A — liaison Cursor

Espace **isolé** du backend produit.

## Contenu versionné

`fixture/` (sources), `lib/`, `scripts/`, `tests/`, `SANDBOX.md`,
`COST_SMOKE.md`, `requirements.txt` (`cursor-sdk==1.0.36`).

## Exclu du dépôt (gitignore)

`.venv/`, `worktrees/`, `artifacts/`, `fixture/.git/`, `*.log`, caches pytest.

## Flux

1. Préparation sans agent : venv, fixture git, tests doubles, auth/models.
2. Lire `COST_SMOKE.md` — **pas de garantie €** côté script.
3. Run payant (Jérôme) : `ALLOW_CURSOR_SMOKE=1` + `run_real_smoke.py`.

## Commandes

Voir `docs/slices/lot-6a.md` et le bloc validation de la réponse agent.
