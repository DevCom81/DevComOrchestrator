# LOT 0 — Fondation locale, projet persistant, HQ démo

## Statut

Implémenté — en attente de validation manuelle (install, tests, smoke UI).

## Objectif

Ouvrir le Command Center en mode démo, voir le HQ (11 agents), créer/consulter/modifier un projet, le retrouver après redémarrage SQLite.

## Critères d’acceptation

- [ ] Badge Mode démo visible
- [ ] 11 personnages + spécialités ARCHITECTURE + statut « Non activé »
- [ ] Budget « Non activé » ; décisions/activité vides ; mission désactivée
- [ ] Nav future « Bientôt » sans faux lien
- [ ] CRUD projet sans suppression ; bornes 80 / 2000
- [ ] Persistance après redémarrage
- [ ] Loading / vide / erreur / confirmation
- [ ] Host/Origin + JSON strict sur mutations
- [ ] Données hors dépôt ; locks générés ; limites de lisibilité OK

## Périmètre exclu

Missions, Dispatcher moteur, budget réel, SSE, LLM, mode personnel, suppression projet, Playwright, mini-journal.

## Fichiers principaux

- `backend/src/devcom/` — domaine projects, catalogue agents, API, sécurité
- `frontend/src/` — shell HQ, projets
- `contracts/agents/catalogue.json`
- `Assets/README.md` + `frontend/public/agents/*.png`
- `docs/adr/0001-stack-fondation-locale.md`
- `scripts/check_size_limits.*`

## Validations

Voir le compte rendu de livraison LOT 0 (commandes manuelles groupées).
