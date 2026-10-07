# ADR 0003 — Revue TECH de démonstration (LOT 2)

- Statut : accepté
- Date : 2026-10-07

## Contexte

Le LOT 1 route des missions sans exécuter d’analyses. Le LOT 2 doit livrer une revue TECH consultable, déterministe, avec propositions, blocage critique et ADR de démonstration — sans second orchestrateur ni moteur IA.

## Décisions

1. **Agrégat `TechReview` distinct** des missions de routage, sous `modules/missions/tech/`, réutilisant Capability Registry et Permission Policy (versions 2) sans registry concurrent.
2. **Scénarios fictifs versionnés** (`contracts/tech/scenarios/`) : `local_persistence` (désaccord conservé, deux propositions ouvertes) et `security_critical` (une proposition bloquée par politique).
3. **Politique de blocage versionnée** (`contracts/tech/blocking_policy.json`) : le moteur calcule `blocked` à partir des findings ; la fixture n’est pas le seul garde-fou.
4. **Snapshot projet figé** à la confirmation de scénario ; immutable ensuite. Après lancement, scénario immutable.
5. **Pipeline synchrone** : préparer et valider les résultats avant écriture atomique (`analyses`, `proposals`, `awaiting_decision`). Pas de worker, SSE ni délais artificiels.
6. **Idempotence** sur création, lancement et décision (clé + hash de payload) ; contraintes uniques décision/ADR par revue.
7. **Décision** : auteur `local-demo-user`, motif obligatoire, effort S/M/L, ADR dans la même transaction, avertissement « n’autorise aucune implémentation ». Aucune levée de blocage critique dans ce lot.
8. Les missions LOT 1 ne lancent pas de revue TECH ; l’API TECH refuse les champs d’affectation forcés (`extra=forbid`).

## Conséquences

- UI TECH active ; SALES/MAIL/SOCIAL restent « Bientôt ».
- Les cartes HQ restent « Non activé ».
- Un scénario choisi pour une demande non reconnue affiche le disclaimer d’analyse non libre.
