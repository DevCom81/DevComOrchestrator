# Roadmap V1 — DevCom Command Center

Date : 2026-10-07 (révision LOT 6A/6B — liaison Cursor obligatoire).  
Sources : `ARCHITECTURE.md`, `AGENTS.md`, ADR 0001–0008, code LOT 0–6, spike 6A.  
Statut : **trajectoire de référence** — 12 lots (0–11) + sous-lots **6A / 6B**.  
Lots 7–11 conservés. **Aucun LOT 7 avant preuve spike 6A.**

## 1. Ligne d’arrivée V1

La V1 est **terminée** quand, depuis le même HQ local (cartes agents + portraits PNG) :

1. **TECH** réel (OpenAI) et démo isolée : budget, sources code, historique durable, interruptions honnêtes.
2. **Décisions TECH** (choix d’option + ADR) distinctes du **GO Cursor** et des **GO d’envoi/publication**.
3. **Approbations** liées à un payload/version/hash exact ; toute modification pertinente invalide le GO.
4. **Parcours Cursor obligatoire** : fondation LOT 6 (paquet/GO/export/import) **et** liaison réelle
   orchestrateur → Cursor → code produit → retour automatique → review dans l’HQ.
   Un blocage documenté **ne remplace pas** cette capacité. Import/export manuel = **dépannage**.
5. **MAIL / SALES / SOCIAL** : parcours **quotidiens réels** (IA bornée si besoin, budget, permissions, persistance, audit). Les fixtures servent à la **démo publique** ; elles ne valident pas les capacités réelles.
6. **Mémoire projet** réutilisable et versionnée, **isolée entre projets** ; **budget commun** à toutes les équipes ; **audit** consultable.
7. **Résolution comptable** des coûts incertains (preuves + historique) — distincte de l’acquittement humain LOT 5.
8. **Sauvegarde/restauration** cohérente (SQLite + artefacts privés, dont snapshots) dans un `data_dir` isolé de test.
9. **Installation neuve** démo + vérification des parcours réels déjà validés ; procédure quotidienne documentée.

**Hors V1 (V2/V3)** : `systemd --user`, planification daemon, notifications D-Bus, **QG animé 2D/3D**.  
Les **portraits PNG** et le **HQ actuel** sont **dans la V1**.  
**Pas de lot silencieux** : tout changement de découpage est explicite ci-dessous.

## 2. Arbitrages

| Arbitrage | Choix | Motif |
|---|---|---|
| Numérotation | 12 lots 0–11 ; Cursor = LOT 6 + **6A/6B** | GO complémentaire 2026-10-07 |
| Portraits / HQ | V1 | Déjà livrés |
| QG 2D/3D immersif | Hors V1 | ARCHI V2/V3 |
| Approbations | Trois natures (TECH ≠ GO Cursor ≠ envoi/publication) | Payload/hash exact |
| Anthropic/Gemini | Hors V1 | OpenAI seul fournisseur réel V1 |
| Cursor | Fondation manuelle LOT 6 ; **liaison SDK obligatoire** (6A preuve, 6B adapter) ; manuel = dépannage | Critère V1 TECH |
| MAIL connecteur | Choix au plan LOT 7 | Pas d’invention d’API |
| SALES recherche | Brave Search API proposée (LOT 8) | GO LOT 8 confirme |
| SOCIAL publication | Export manuel V1 ; native si API prouvée | ARCHI |
| Coûts incertains | Ack = LOT 5 ; résolution comptable = LOT 10 | Pas de nouveau lot |
| Fixtures | Démo publique seulement | ≠ preuve du réel |

**Impact découpage** : pas de 13ᵉ lot. **6A/6B** sont des sous-lots de Cursor avant MAIL. Lots 7–11 inchangés.

## 3. Écarts architecture ↔ implémentation

| Engagement | État |
|---|---|
| HQ + portraits PNG | Livré (0) |
| Capability / permissions / Dispatcher | Livré (1) |
| TECH démo | Livré (2) |
| Budget µEUR, OpenAI réel | Livré (3) |
| Contexte code / snapshot | Livré (4) |
| Durabilité / events / SSE | Validé (5) |
| Plan Cursor / GO hash / export / retour | Fondation livrée (6) — validation manuelle |
| Liaison Cursor SDK (preuve) | → **LOT 6A** |
| Adapter Cursor intégré | → **LOT 6B** (après 6A vert) |
| MAIL / SALES / SOCIAL réels | → LOT 7–9 |
| Résolution comptable / backup | → LOT 10 |
| Gate démo + réel | → LOT 11 |

## 4. Lots 0–5 validés / 6 fondation

| Lot | Objectif | Statut |
|---|---|---|
| 0–4 | Fondation → code | Validés |
| 5 | Durabilité / SSE | Validé |
| **6** | Paquet Cursor, GO, export/import manuel | Livré (fondation) — à valider manuellement |

## 5. LOT 6 — Fondation (conservée)

- Paquet versionné, preview, GO hash, export MD+manifeste, import rapport/diff, vérif structurelle, revue retour sans run auto.
- Voir `docs/slices/lot-6.md`, ADR 0007.
- **Acquis conservés** ; pas de refonte.

## 6. LOT 6A — Spike liaison Cursor (preuve)

- **Objectif** : prouver bout en bout sur dépôt fixture isolé, sans toucher les projets quotidiens.
- **Preuve de succès** (obligatoire) :
  1. paquet approuvé (contrat LOT 6) ;
  2. invocation Cursor (SDK local) ;
  3. modification demandée **obtenue** dans le worktree ;
  4. **ensemble des changements** récupéré automatiquement (suivis, indexés, **fichiers nouveaux**) ;
  5. retour rattaché au bon `export_id` ;
  6. validation locale autorisée (commande + exit code + logs) consultable.
- `finished` / `cancelled` seuls **ne suffisent pas**. Cancel valide seulement le scénario d’arrêt.
- **Isolation** : worktree/clone ≠ sandbox OS. Politique explicite (fichiers, réseau, commandes, secrets, env minimal). Fixture sans données personnelles. Pas d’env backend complet. Pas d’écriture projets quotidiens. Pas de push.
- **Crash** : reconnect ≠ nouveau `send` ; aucun `send` auto après interruption ; `resume` local non promis sans preuve ; état **incertain** si récupération impossible.
- **Budget** : un seul run micro smoke, **sans retry auto**. Avant run payant : modèle, plafond effectif, coût max garanti ou limites de la garantie. Timeout ≠ plafond financier.
- **Autorisation actuelle** : docs, préparation, doubles, venv épinglé — **aucun run payant** tant que Jérôme n’a pas validé coût/périmètre.
- Voir `docs/slices/lot-6a.md`, ADR 0008, `spikes/cursor_lot6a/`.

## 7. LOT 6B — Adapter intégré (après 6A)

- Port/adapter dans le monolithe ; UI invoke/suivi/cancel ; budget applicatif ; manuel en dépannage.
- **Interdit** avant preuve 6A verte.
- Voir `docs/slices/lot-6b.md` (plan ; pas de code prod avant GO 6B).

## 8. Lots 7–11 (numéros et périmètre conservés)

### LOT 7 — MAIL quotidien réel

- **Objectif** : traiter les mails du jour sous contrôle humain, réellement.
- **Connecteur** : choisi au plan du lot selon la messagerie effective ; mode fichier = démo publique seulement.
- **Périmètre** : lecture/classement/résumé (IA bornée si besoin), brouillon, GO d’envoi distinct, audit.
- **GO envoi** : destinataires + compte + corps + pièces (refs/hash) + version ; modification → invalidation.
- **Exclusions** : suppression auto spam ; envoi sans GO ; fixtures seules comme preuve.
- **Acceptation** : envoi réel seulement après GO valide ; résultat traçable.
- **Prérequis** : preuve spike LOT 6A avant de démarrer ce lot.

### LOT 8 — SALES réel

- **Objectif** : qualifier un prospect sourcé et préparer un contact.
- **Recherche proposée** : Brave Search API (bornée, URLs + dates). Confirmation au GO LOT 8.
- **Périmètre** : critères, recherches datées, dossier, brouillon, relais MAIL (GO = LOT 7).
- **Exclusions** : envoi direct SALES ; identité sans preuve ; fixtures seules.
- **Acceptation** : chaque fiche a source+date ; pas d’envoi hors GO MAIL.

### LOT 9 — SOCIAL

- **Objectif** : préparer la publication du jour.
- **Périmètre** : idées, variantes, version choisie, calendrier ; export/copier manuel (V1) ; native optionnelle si API prouvée.
- **Exclusions** : faux succès ; fixtures seules comme preuve d’un connecteur natif.
- **Acceptation** : variantes non clones ; export utilisable.

### LOT 10 — Sauvegarde, restauration, résolution comptable, installation

- **Objectif** : ne pas perdre l’état ; clore les incertitudes budgétaires avec preuves.
- **Backup** : SQLite + artefacts privés (dont snapshots).
- **Restore** : `data_dir` distinct — sans effacer les données quotidiennes.
- **Secrets** : exclus du backup versionné.
- **Résolution comptable** : distincte de l’ack LOT 5 ; preuves ; aucun « pris en compte » seul.
- **Acceptation** : backup → restore isolé OK ; ≥ 1 résolution d’incertain avec preuve.

### LOT 11 — Stabilisation et démonstration publique V1

- **Objectif** : dépôt public démontrable ; gate V1.
- **Périmètre** : install neuve démo ; relecture parcours réels sans débits inutiles ; procédure quotidienne ; limites documentées.
- **Exclusions** : données personnelles ; secrets ; V2/V3.
- **Acceptation** : checklist §10 ; clone neuf démo OK.

## 9. Tableau synthétique

| # | Statut | Thème |
|---:|---|---|
| 0–4 | Validés | Fondation → code |
| 5 | Validé | Durabilité / SSE |
| 6 | Fondation livrée | Paquet / GO / export / retour |
| **6A** | Validé | Spike liaison Cursor (preuve) |
| **6B** | Implémenté | Adapter Cursor intégré (validation manuelle) |
| 7 | À valider | MAIL réel |
| 8 | À valider | SALES + Brave |
| 9 | À valider | SOCIAL |
| 10 | À valider | Backup + comptable |
| 11 | À valider | Gate V1 |

**Total : 12 lots (0–11) + sous-lots 6A/6B.**

## 10. Définition vérifiable « V1 terminée »

- [ ] HQ + portraits ; TECH démo + réel durable
- [ ] Décision TECH ≠ GO Cursor ≠ GO envoi/publication
- [ ] **Liaison Cursor réelle** (6A preuve + 6B intégré) : invoke → code → retour auto → review
- [ ] Manuel export/import = dépannage uniquement
- [ ] MAIL réel + mode fichier démo
- [ ] SALES sourcé + relais MAIL
- [ ] SOCIAL exportable ; native si prouvée
- [ ] Mémoire isolée ; budget commun ; audit
- [ ] Résolution comptable des incertains
- [ ] Backup/restore isolé ; secrets hors backup
- [ ] Install neuve démo + preuves sans débits inutiles
- [ ] Procédure quotidienne ; aucun item V2/V3 requis

## 11. Prochaines étapes

1. Valider manuellement la fondation **LOT 6** (si pas déjà fait).
2. Exécuter la préparation **6A** (venv, doubles) — commandes dans `docs/slices/lot-6a.md`.
3. Jérôme lance le **premier run réel** après présentation coût + périmètre.
4. Si 6A vert → plan détaillé + GO **6B**.
5. **Pas de LOT 7** avant preuve 6A.
