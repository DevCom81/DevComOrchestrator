# ADR 0008 — Liaison Cursor SDK obligatoire en V1 TECH

## Statut

Accepté — 2026-10-07 (GO documentation + préparation spike 6A).

## Contexte

Le LOT 6 a livré la fondation : paquet versionné, GO hash, export/import manuel,
vérification structurelle, revue retour. Le parcours quotidien voulu est cependant :

prompt orchestrateur → spécialistes → revue → GO → Cursor code → retour → review.

Le transfert manuel seul ne satisfait pas ce parcours. Les docs Cursor documentent
un SDK public beta (`cursor-sdk` / `@cursor/sdk`) avec runtimes local et cloud,
stream, cancel et usage — sans inventer d’API.

## Décision

1. **Critère V1 TECH** : liaison réelle orchestrateur → Cursor → code → retour →
   review est **obligatoire**. Un blocage documenté ne la remplace pas.
2. **Sous-lots** : **6A** = preuve (spike) ; **6B** = adapter intégré. Lots 7–11
   inchangés. Pas de MAIL avant preuve 6A.
3. **Manuel** : export/import LOT 6 restent le **dépannage**, pas le nominal V1.
4. **Preuve 6A** : modification demandée obtenue + capture automatique des
   changements (suivis, indexés, nouveaux) + retour rattaché à l’export +
   validation locale (commande, exit, logs). Statut SDK seul insuffisant.
5. **Isolation** : worktree/clone ≠ sandbox OS. Politique explicite (fichiers,
   réseau, commandes, secrets, env minimal). Fixture sans données personnelles.
   Pas d’écriture sur projets quotidiens ; pas de push.
6. **Crash** : reconnect ≠ nouveau `send` ; aucun `send` auto après interruption ;
   `resume` local non promis sans preuve ; état incertain si récupération impossible.
7. **Budget** : un run micro smoke sans retry auto ; coût/plafond présentés avant
   toute invocation payante. Timeout ≠ plafond financier.

## Conséquences

- `docs/ROADMAP_V1.md`, `ARCHITECTURE.md`, slices `lot-6a` / `lot-6b`.
- Spike sous `spikes/cursor_lot6a/` (venv épinglé, doubles, capture).
- Adapter prod uniquement au GO 6B après spike vert.
