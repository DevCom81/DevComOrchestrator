# LOT 6B — Adapter Cursor intégré

## Statut

Plan uniquement — **interdit** avant preuve LOT 6A verte + GO 6B explicite.

## Objectif

Intégrer dans le monolithe DevCom un port/adapter Cursor qui réutilise la
fondation LOT 6 (paquet, GO, export, retour) pour le parcours nominal :

invoke → suivi/cancel → capture changements → retour rattaché → validation
locale → revue. Import/export manuel = dépannage UI.

## Périmètre prévu (après GO)

- Port `CursorAgentPort` (create/send/stream/cancel/status) ; adapter SDK Python.
- Worktree isolé par run ; politique sandbox versionnée.
- Capture complète (suivis / indexés / nouveaux) + artefacts hashés.
- Budget : réservation avant `send` ; un run sans retry auto par défaut.
- Événements durables (pattern LOT 5) ; états interrupted / uncertain.
- UI : lancer, suivre, arrêter, consulter preuves (pas le texte agent comme vérité).

## Exclusions

MAIL ; push ; apply sur projets quotidiens sans GO ; nouveau `send` auto ;
dépendance non épinglée ; démarrage avant 6A vert.

## Acceptation (cible)

Parcours HQ : décision TECH → plan → GO → invoke Cursor → retour auto →
validation locale visible → revue retour. Manuel disponible si SDK down.
