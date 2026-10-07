# LOT 3 — Revue TECH réelle OpenAI + budget + runner supervisé

## Statut

Implémenté — smoke OpenAI réussi (analyses/critiques/synthèse + coûts confirmés).
Finition UI : titre navigateur selon mode, grille spécialistes 1–3 colonnes, états
« aucune observation » / « résultat absent », bannière statut/synthèse/budget,
libération réservation (`settled`) en fin normale.

## Objectif

Activer des revues TECH réelles via OpenAI Responses, avec graphe spécialiste borné (max 19 appels), réservation budgétaire µEUR, runner serveur in-process supervisé, polling UI, isolation totale de la démo LOT 2.

## Critères d’acceptation

- [ ] Mode Démo/Réel ; réel désactivé par défaut ; clé OPENAI présente/absente (jamais exposée)
- [ ] Enveloppe max 19 appels recalculée ; refus si > 1 € ; plafonds 50 €/mois et 1 €/revue
- [ ] 6 analyses + critiques + réponses ciblées + synthèse ; Synthétiseur ne parle pas à la place des spécialistes
- [ ] POST lance une tâche supervisée ; GET/polling sans appel ; un process / une revue réelle active
- [ ] Crash : résultats terminés conservés ; in_flight → uncertain ; pas de reprise/rejeu auto
- [ ] Usage enregistré même si résultat invalide ; pas de double compte reasoning ; mois Europe/Paris
- [ ] UI complète : budget HQ, étapes, coûts, erreurs, partiels, incertains
- [ ] Tests doubles (pas d’appel payant agent) ; smoke réel manuel ≤ 1 €

## Décisions clés

Voir `docs/adr/0004-tech-real-openai-budget.md` et `contracts/billing/COST_ENVELOPE_LOT3.md`.

## Périmètre exclu (reporté)

SSE/worker durable multi-process, retries payants, outils externes, LOT 4, réparation IA automatique, levée de blocage critique.
