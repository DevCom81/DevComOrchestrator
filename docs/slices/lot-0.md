# LOT 0 — Fondation locale, projet persistant, HQ démo

## Statut

**Validé** (technique + utilisateur) — 2026-10-07.

## Objectif

Ouvrir le Command Center en mode démo, voir le HQ (11 agents), créer/consulter/modifier un projet, le retrouver après redémarrage SQLite.

## Critères d’acceptation

- [x] Badge Mode démo visible
- [x] 11 personnages + spécialités ARCHITECTURE + statut « Non activé »
- [x] Budget « Non activé » ; décisions/activité vides
- [x] CRUD projet sans suppression ; bornes 80 / 2000
- [x] Persistance après redémarrage
- [x] Loading / vide / erreur / confirmation
- [x] Host/Origin + JSON strict sur mutations
- [x] Données hors dépôt ; locks ; limites de lisibilité OK

## Périmètre exclu (reporté)

Missions, Dispatcher moteur, budget réel, SSE, LLM, mode personnel, Playwright.
