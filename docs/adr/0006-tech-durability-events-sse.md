# ADR 0006 — Durabilité TECH, événements, SSE

## Statut

Accepté — LOT 5 (2026-10-07).

## Contexte

Après LOT 3–4, un crash peut laisser une revue `running` sans étape `in_flight`.
Il faut distinguer interruption propre et coût/appel incertain, journaliser les
transitions, et permettre reconnexion UI sans nouvel appel LLM.

## Décision

- Statuts : `interrupted` (arrêt sans appel/coût ambigu) vs `blocked_uncertain`
  (au moins un appel ou coût réellement incertain).
- `in_flight` persisté **avant** l’appel fournisseur.
- Résultat d’étape + usage + transition + événement dans **une transaction**
  SQLite (appel réseau hors transaction).
- Reconcile boot idempotent : pas de doublon d’événement, pas de double
  libération, pas de nouveau débit, pas de reprise LLM.
- Budget : libérer seulement ce dont la non-exécution est prouvée ; conserver
  la réserve des appels ambigus ; acknowledge humain ≠ confirmation fournisseur
  et ≠ libération ambiguë.
- Journal `tech_review_events` (seq monotone) ; SSE + `GET .../events` ;
  polling de secours. Payloads sans secrets ni contenus source.
- Un process / une revue réelle active inchangé.

## Conséquences

- UI : timeline, bannières interruption/incertitude, liste revues sur Projet.
- Pas de garantie at-least-once fournisseur ; incertitude explicite après coupure.

## Alternatives rejetées

- Tout mapper sur `blocked_uncertain`.
- Retry / reprise automatique.
- Worker distribué.
