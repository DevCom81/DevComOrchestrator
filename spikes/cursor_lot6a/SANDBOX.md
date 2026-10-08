# Politique sandbox — spike LOT 6A

Un worktree Git **isole les commits/diffs**, pas les accès système.
Cette fiche fixe le périmètre **visé** pour le smoke ; le résultat réel du
SDK (sandbox Cursor) sera consigné après le premier run.

## Fichiers

- Lecture/écriture : uniquement le répertoire worktree sous
  `spikes/cursor_lot6a/worktrees/<run_id>/`.
- Interdit : dépôt DevComOrchestrator hors ce spike, `~/` projets quotidiens,
  `data/` backend, secrets, boîtes mail.

## Réseau

- L’agent SDK contacte les services Cursor (facturation / modèles) — hors
  contrôle local total.
- Pas d’autre cible réseau volontaire dans le prompt fixture.
- Consigne au smoke : noter si des outils réseau ont été utilisés.

## Commandes

- Autorisées pour **validation orchestrateur** (hors agent) :
  `python -m pytest` dans le worktree fixture uniquement.
- Toute autre commande agent : à journaliser ; refuser push (`git push`).

## Secrets et environnement

- `CURSOR_API_KEY` : dans l’environnement du **script smoke** seulement,
  jamais dans le prompt ni dans les artefacts versionnés.
- Ne **pas** transmettre l’environnement complet du backend DevCom
  (pas de `DEVCOM_*`, pas de `.env`, pas de `DATABASE_URL`).
- Env minimal transmis si besoin : `PATH`, `HOME` générique, `LANG`, cwd worktree.

## Git

- Pas de `git push`, pas de remote obligatoire sur le fixture.
- Capture orchestrateur : suivis + index + non suivis (nouveaux).

## Smoke réel (`run_real_smoke.py`)

- Clone neuf : `worktrees/smoke-1/` (détruit/recréé à chaque lancement).
- `SandboxOptions(enabled=True)` demandé au SDK ; résultat effectif à
  constater dans les logs/artefacts — ne pas le sur-promettre.
- `setting_sources=("project",)` uniquement (pas user/team/mdm).
- Scrub process : retire `DEVCOM_*`, `DATABASE_URL`, clés LLM backend.
- `CURSOR_API_KEY` reste pour le SDK ; jamais écrite dans les artefacts.
