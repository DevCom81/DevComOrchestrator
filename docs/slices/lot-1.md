# LOT 1 — Capacités, permissions, Dispatcher démo, mission bornée

## Statut

**Validé** (technique + utilisateur) — 2026-10-07.

## Objectif

Créer une mission liée à un projet, obtenir un routage démo déterministe expliqué, clarifier si besoin, refuser les affectations hors compétence, bloquer les intentions EXTERNAL sans exécution, persister après redémarrage.

## Critères d’acceptation

- [x] « Classer ces mails » → Secrétaire ; QA exclu
- [x] « Concevoir la persistance SQLite » → SQL/Data + Architecte ; Vendeur exclu
- [x] Demande mixte → tâches commercial / technique séparées
- [x] « Envoyer ce mail au client » → `blocked_authorization`, sans ApprovalRequest ni exécution
- [x] Demande inconnue → clarification structurée ; token obsolète refusé
- [x] Disclaimer routage démo visible
- [x] HQ agents toujours « Non activé » ; pas de bouton lancer les analyses
- [x] Persistance + FK SQLite ; limites lisibilité

## Décisions clés

Voir `docs/adr/0002-capability-permission-demo-dispatch.md`.
