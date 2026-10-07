# ADR 0005 — Contexte code local, preview figé et snapshot immuable

## Statut

Accepté — LOT 4 (2026-10-07).

## Contexte

Les revues TECH LOT 2–3 ne disposaient que d’un snapshot métadonnées projet.
Il faut rattacher un dossier local en lecture seule, prévisualiser le paquet
exact destiné aux agents, puis figer un snapshot vérifiable sans appel
fournisseur avant lancement.

## Décision

- Module `projects` propriétaire du root, exclusions, preview et snapshot.
- Preview (`preview_id`) copie les contenus choisis sous `DEVCOM_DATA_DIR`,
  calcule empreintes et expire ; le freeze **ne relit pas** la source :
  il promeut les copies preview ou refuse si empreinte/expiration invalides.
- Contrôle chemin par composants + refus symlink (y compris intermédiaires) ;
  fichiers réguliers uniquement ; exploration bornée et paginée.
- Exclusions dures + projet + `.gitignore` (parse local, sans exécuter le dépôt).
- Comptage bloquant : `utf8_byte_upper_bound` (plafond BPE justifié). `char/4`
  indicatif seulement. Sinon refus.
- Enveloppe LOT 3 recalculée sur payloads complets (contexte répété dans les
  analyses) + `max_output` ; max 19 appels ; pas d’augmentation silencieuse du
  plafond revue 1 € ; aperçu ne réserve rien.
- Revue sans code autorisée avec mention explicite.
- Trajectoire : LOT 4 = contexte code ; SSE/durabilité **reportés**.

## Conséquences

- UI Projet : rattachement → exploration → sélection → aperçu intégral → freeze.
- UI Revue : panneau Sources + bandeau si aucune source fichier.
- Tests doubles FS ; zéro appel OpenAI dans la validation agent.

## Alternatives rejetées

- Relire le disque au freeze (course silencieuse).
- Préfixe `realpath` seul (contournement symlink/TOCTOU).
- Troncature silencieuse ou `char/4` comme garantie.
- Clonage distant / outils d’exécution dans le dépôt.
