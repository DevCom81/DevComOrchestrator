# ADR 0004 — Revue TECH réelle OpenAI, budget et runner supervisé

## Statut

Accepté — LOT 3 (2026-10-07).

## Contexte

Le LOT 2 livre une revue TECH démo déterministe. Le LOT 3 active des appels OpenAI réels sans inventer une voix collective, sans retries payants, et avec une enveloppe budgétaire bornée.

## Décision

- API **OpenAI Responses**, Structured Outputs, `max_retries=0`, aucun outil externe.
- Modèles : `gpt-6-luna` (effort `none`) pour Cyber/QA/DevOps/FullStack/SQL-Data ; `gpt-6.1-sol` (effort `low`) pour Architecte et Synthétiseur.
- Contradiction spécialisée : 6 analyses → 6 critiques (≤1 objection) → réponses ciblées (sautées si aucune objection) → 1 synthèse. Maximum **19** appels.
- Réservation de l’enveloppe max (19 appels, tarif entrée = max(uncached, cache_write), uplift régional 10 %, FX ECB + marge 5 %) avant tout appel. Si enveloppe > 1 € → refus explicite.
- Montants en micro-unités entières (µUSD / µEUR). FX re-vérifié le 2026-10-07 : `1 USD = 0.88739 EUR` (date taux 2026-10-06).
- Runner **in-process supervisé** : POST persiste le plan, réserve, démarre un thread suivi ; GET/polling ne déclenche aucun appel. Une revue réelle active par process (verrou SQLite).
- Crash : étapes `in_flight` → `uncertain` ; pas de reprise automatique ; dépendances bloquées.
- Mode réel désactivé par défaut (`DEVCOM_MODE=demo`). Clé via `OPENAI_API_KEY` (présence seule exposée à l’UI).
- Démo LOT 2 inchangée et isolée.

## Conséquences

- UI affiche mode, clé présente/absente, budget HQ, étapes, coûts confirmés/incertains, échecs partiels.
- Pas d’appel payant dans les tests (FakeLlm). Smoke réel manuel sous 1 €.
- Réconciliation coût ≠ reprise de workflow.

## Alternatives rejetées

- Appel collectif multi-agents : invente les avis.
- Worker détaché / Celery / Redis : hors besoin V1.
- Retry automatique fournisseur : risque double facturation.
- SSE pour LOT 3 : polling suffit.
