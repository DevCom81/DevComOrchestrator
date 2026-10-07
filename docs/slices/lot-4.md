# LOT 4 — Contexte code local vérifiable pour revue TECH

## Statut

Implémenté — en attente de validation manuelle (doubles, pas d’appel payant agent).

## Objectif

Rattacher un dossier local à un Projet, sélectionner des fichiers, prévisualiser
le paquet exact (contenu intégral, taille, estimation), figer un snapshot
immuable et l’associer à une Revue TECH, sans envoi OpenAI avant lancement.

## Relation

- **Projet** : mémoire + sources (root, exclusions, previews, snapshots).
- **Mission (LOT 1)** : routage Dispatcher — pas d’exécution TECH.
- **Revue TECH** : analyses spécialisées consommant un snapshot projet (± code).

## Critères d’acceptation

- [ ] Rattacher/détacher un root depuis le détail Projet
- [ ] Explorer sous root uniquement ; symlinks / spéciaux / `..` refusés
- [ ] Preview avec `preview_id`, empreinte, expiration ; contenu intégral
- [ ] Freeze = copies preview (pas de relecture source) ; refus si expiré/altéré
- [ ] Exclusions dures + projet + gitignore ; bornes signalées sans troncature
- [ ] Revue sans code : mention « Aucune source fichier… »
- [ ] Enveloppe recalculée sur payloads ; aperçu sans réservation ni appel
- [ ] Sources affichées sur la revue ; evidence_refs limitées au snapshot
- [ ] Isolation démo (fixture) / réel ; budget LOT 3 conservé
- [ ] Tests doubles : changement post-preview, symlink, spéciaux, limites, isolation

## Exclusions (reportées)

Clonage distant, modification de code, SSE/worker durable, GO Cursor, retries payants.

## Décisions

Voir `docs/adr/0005-code-context-snapshot.md`, `contracts/filesystem/`.
