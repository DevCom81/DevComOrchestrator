# ADR 0009 — Exécution Cursor intégrée et intégration locale contrôlée

## Statut

Accepté — LOT 6B (2026-10-08).

## Contexte

LOT 6A a prouvé la liaison SDK locale. LOT 6 fournit paquet/GO export/retour.
Il faut un parcours produit : GO execute distinct, exécution durable, retour
auto, corrections bornées, branche locale sans merge/push implicites.

## Décision

1. GO `cursor.plan.execute` : paquet + base Git propre (commit) + modèle +
   sandbox + validations + réservation budgétaire ; chaque `send` = nouveau GO.
2. Corrections ≤ 2 / `plan_version` (compteur persisté) ; contexte = paquet +
   observations + capture précédente.
3. Intention persistée avant invoke ; GO+réserve+création atomiques ;
   idempotency sur start ; cancel demandé ≠ confirmé ; capture seulement si
   écritures stables sinon `capture_incomplete`.
4. Adapter `fake` explicite en démo/tests ; mode réel exige `real` + clé —
   jamais Fake silencieux.
5. Intégration : worktree isolé sur le **source root attaché**, branche
   `devcom/cursor/<execution_id>`, commit local, pas de merge/push.
6. Budget : réservation DevCom ≠ coût Cursor ≠ garantie fournisseur.
7. `.env` local + `.env.example` ; démarrage `scripts/devcom_start.sh demo|real`.

## Conséquences

Migration `0008`, UI exécution/intégration, `cursor-sdk==1.0.36` en deps,
tests doubles LOT 6B.
