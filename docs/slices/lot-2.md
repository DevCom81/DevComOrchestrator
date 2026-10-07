# LOT 2 — Revue TECH démo, propositions, ADR

## Statut

Implémenté — en attente de validation manuelle.

## Objectif

Créer une revue TECH distincte du routage LOT 1, sélectionner un scénario fictif, lancer un pipeline synchrone déterministe, consulter les six spécialistes / contradictions / synthèse / propositions, enregistrer une décision humaine et une ADR de démonstration, avec idempotence et blocage critique.

## Critères d’acceptation

- [ ] Agrégat TechReview distinct ; mêmes contrôles compétences/permissions que le lot 1
- [ ] Scénario A : deux propositions ouvertes + désaccord conservé
- [ ] Scénario B : une proposition bloquée (risque critique) + alternative ouverte ; pas de levée
- [ ] Snapshot figé à la confirmation ; inchangé si le projet est modifié ensuite
- [ ] Demande non reconnue + scénario choisi → disclaimer d’analyse non libre
- [ ] Idempotence création / lancement / décision ; conflit clé/payload ; une seule ADR
- [ ] Refus sélection bloquée et version obsolète côté serveur
- [ ] UI TECH complète ; SALES/MAIL/SOCIAL « Bientôt » ; HQ « Non activé »
- [ ] Persistance après redémarrage ; pas de résultats partiels après échec

## Décisions clés

Voir `docs/adr/0003-tech-review-demo.md`.

## Périmètre exclu (reporté)

Levée de blocage, GO d’implémentation, worker/SSE, appels IA réels, LOT 3.
