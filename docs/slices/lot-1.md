# LOT 1 — Capacités, permissions, Dispatcher démo, mission bornée

## Statut

Implémenté — en attente de validation manuelle.

## Objectif

Créer une mission liée à un projet, obtenir un routage démo déterministe expliqué, clarifier si besoin, refuser les affectations hors compétence, bloquer les intentions EXTERNAL sans exécution, persister après redémarrage.

## Critères d’acceptation

- [ ] « Classer ces mails » → Secrétaire ; QA exclu
- [ ] « Concevoir la persistance SQLite » → SQL/Data + Architecte ; Vendeur exclu
- [ ] Demande mixte → tâches commercial / technique séparées
- [ ] « Envoyer ce mail au client » → `blocked_authorization`, sans ApprovalRequest ni exécution
- [ ] Demande inconnue → clarification structurée ; token obsolète refusé
- [ ] Disclaimer routage démo visible
- [ ] HQ agents toujours « Non activé » ; pas de bouton lancer les analyses
- [ ] Persistance + FK SQLite ; limites lisibilité

## Décisions clés

Voir `docs/adr/0002-capability-permission-demo-dispatch.md`.
