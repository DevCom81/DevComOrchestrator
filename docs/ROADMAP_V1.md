# Roadmap V1 — DevCom Command Center

Date : 2026-10-07 (révision après validation humaine).  
Sources : `ARCHITECTURE.md`, `AGENTS.md`, ADR 0001–0006, code LOT 0–5, GO LOT 5.  
Statut : **trajectoire de référence validée** — 12 lots (0–11).  
LOT 5 conserve son GO ; **lots 6–11 à valider individuellement avant code**.

## 1. Ligne d’arrivée V1

La V1 est **terminée** quand, depuis le même HQ local (cartes agents + portraits PNG) :

1. **TECH** réel (OpenAI) et démo isolée : budget, sources code, historique durable, interruptions honnêtes.
2. **Décisions TECH** (choix d’option + ADR) distinctes du **GO Cursor** et des **GO d’envoi/publication**.
3. **Approbations** liées à un payload/version/hash exact ; toute modification pertinente invalide le GO.
4. **Plan Cursor** : prévisualisation exacte, GO distinct, export manuel, retour de diff/revue.
5. **MAIL / SALES / SOCIAL** : parcours **quotidiens réels** (IA bornée si besoin, budget, permissions, persistance, audit). Les fixtures servent à la **démo publique** ; elles ne valident pas les capacités réelles.
6. **Mémoire projet** réutilisable et versionnée, **isolée entre projets** ; **budget commun** à toutes les équipes ; **audit** consultable.
7. **Résolution comptable** des coûts incertains (preuves + historique) — distincte de l’acquittement humain LOT 5.
8. **Sauvegarde/restauration** cohérente (SQLite + artefacts privés, dont snapshots) dans un `data_dir` isolé de test.
9. **Installation neuve** démo + vérification des parcours réels déjà validés ; procédure quotidienne documentée.

**Hors V1 (V2/V3)** : `systemd --user`, planification daemon, notifications D-Bus, **QG animé 2D/3D** et évolutions immersives.  
Les **portraits PNG** et le **HQ actuel** sont **dans la V1** (déjà livrés LOT 0).  
Aucun ajout hors architecture pour « remplir » la roadmap. **Pas de lot silencieux** : tout changement de découpage est explicite ci-dessous.

## 2. Arbitrages

| Arbitrage | Choix | Motif |
|---|---|---|
| Numérotation | 12 lots 0–11 ; LOT 5 = durabilité/SSE ; Cursor = LOT 6 | GO + validation roadmap |
| Portraits / HQ | V1 (identité visuelle) | Déjà livrés ; distincts du QG animé |
| QG 2D/3D immersif | Hors V1 | ARCHI V2/V3 |
| Approbations | Contrat commun, **trois natures** (décision TECH ≠ GO Cursor ≠ GO envoi/publication) | Payload/hash exact |
| Anthropic/Gemini | Hors V1 | Un fournisseur réel (OpenAI) |
| Cursor auto | Export manuel V1 | Preuve avant automation |
| MAIL connecteur | **Choix au plan LOT 7** selon la messagerie effective de Jérôme | Pas d’invention d’API |
| SALES recherche | **Brave Search API** proposée (voir LOT 8) | Sourcé, borné, daté ; GO LOT 8 confirme |
| SOCIAL publication | Export manuel V1 ; native optionnelle si API prouvée | ARCHI |
| Coûts incertains | Ack humain = LOT 5 ; **résolution comptable = LOT 10** | Pas de nouveau lot |
| Fixtures | Démo publique seulement | Ne valident pas le réel |

**Impact découpage** : la résolution comptable reportée du LOT 5 est **absorbée dans le LOT 10** (intégrité d’état + audit). Aucun 13ᵉ lot.

## 3. Écarts architecture ↔ implémentation

| Engagement | État |
|---|---|
| HQ + portraits PNG | Livré (0) — V1 |
| Capability / permissions / Dispatcher | Livré (1) |
| TECH démo | Livré (2) |
| Budget µEUR, OpenAI réel | Livré (3) |
| Contexte code / snapshot | Livré (4) |
| Durabilité / events / SSE | LOT 5 (GO, en validation) |
| Mémoire projet riche (stack, règles…) | Partielle (projet + snapshot) → à enrichir lots suivants |
| Budget multi-équipes commun | Fondations LOT 3 ; étendre à MAIL/SALES/SOCIAL |
| Plan Cursor / GO hash | → LOT 6 |
| MAIL / SALES / SOCIAL réels | → LOT 7–9 |
| Résolution comptable incertains | → LOT 10 (pas LOT 5) |
| Backup SQLite + artefacts | → LOT 10 |
| Gate démo + réel | → LOT 11 |
| Compte mail / Brave / LinkedIn | À confirmer aux lots concernés (ARCHI §15) |

## 4. Lots 0–4 validés

| Lot | Objectif utilisateur | Démo |
|---|---|---|
| **0** | Démarrer localement, HQ + portraits, créer un projet | HQ + projet SQLite |
| **1** | Routage borné, refus hors compétence | QA refuse spam |
| **2** | Revue TECH fictive jusqu’à ADR | Scénario démo |
| **3** | Revue réelle sous enveloppe ≤ 1 € | Smoke OpenAI + FakeLlm |
| **4** | Attacher code, snapshot, lier à la revue | Preview → freeze → sources |

## 5. LOT 5 — autorisé (durabilité)

**Objectif** : quitter l’onglet / redémarrer sans faux « en cours » ; 0 LLM sur GET/SSE/refresh.

**Périmètre** : `interrupted` vs `blocked_uncertain` ; journal ; reconcile idempotent ; budget selon matrice ; SSE + polling ; UI timeline + liste projet ; **acquittement humain** (motif/date) sans libérer la réserve ambiguë ni confirmer un coût.

**Exclusions** : retry LLM, reprise auto, **résolution comptable fournisseur** (→ LOT 10), Plan Cursor.

**Critères mémoire/budget déjà applicables** : usage et réservation persistés ; audit d’événements consultable sur la revue ; isolation démo/réel conservée.

Voir `docs/slices/lot-5.md`.

## 6. Lots 6–11 (propositions — GO individuel requis)

### LOT 6 — Plan Cursor, GO distinct, export, retour

- **Objectif** : prévisualiser le paquet Cursor exact, exporter après GO, importer un rapport/diff.
- **Approbations** : **GO Cursor** ≠ décision TECH (choix d’option). GO lié au hash du paquet ; édition du plan → GO invalidé.
- **Périmètre** : ApprovalRequest (payload, version, hash, expiration, auteur) ; preview ; export ; import ; pas de modif auto du dépôt.
- **Exclusions** : agent Cursor autonome non prouvé ; push git.
- **Mémoire/budget** : plan versionné rattaché au projet ; aucun appel LLM d’export.
- **Acceptation** : sans GO → pas d’export ; GO consommé une fois ; hash mismatch refusé.
- **Démo** : revue → option → preview → GO → fichier.

### LOT 7 — MAIL quotidien réel

- **Objectif** : traiter les mails du jour sous contrôle humain, **réellement**.
- **Connecteur** : choisi **au plan du lot** selon la messagerie effective (IMAP / API fournisseur…) ; mode fichier = démo publique seulement.
- **Périmètre** : lecture/classement/résumé (IA bornée si besoin), brouillon, **GO d’envoi** distinct, audit.
- **GO envoi** : payload exact = destinataires + compte expéditeur + corps + **pièces jointes** (refs/hash) + version ; modification → invalidation.
- **Exclusions** : suppression auto spam ; envoi sans GO ; valider le réel via fixtures seules.
- **Mémoire/budget** : rattachement projet si pertinent ; coûts IA sur **budget commun** ; journal d’audit.
- **Acceptation** : envoi réel seulement après GO valide ; résultat traçable ; fixtures ≠ preuve du connecteur.
- **Démo publique** : fichier démo. **Preuve réelle** : envoi borné manuel hors fixtures.

### LOT 8 — SALES réel

- **Objectif** : qualifier un prospect **sourcé** et préparer un contact.
- **Recherche proposée** : **Brave Search API** (requêtes web bornées, URLs + dates persistées).
  - Limites : quotas/plafond budget ; snippets ≠ identité prouvée ; pas de scraping LinkedIn ; pas d’e-mail inventé ; dédoublonnage obligatoire.
  - Confirmation compte/tarif/plafond au **GO LOT 8** (peut être remplacé si preuve d’un autre moteur équivalent).
- **Périmètre** : critères, recherches datées, dossier, brouillon, **relais MAIL** (GO envoi = LOT 7).
- **Exclusions** : envoi direct SALES ; identité sans preuve ; fixtures comme seule validation.
- **Mémoire/budget** : fiches isolées par projet ; coûts recherche+IA sur budget commun ; audit.
- **Acceptation** : chaque fiche a source+date ; pas d’envoi hors GO MAIL.
- **Démo publique** : prospect fictif. **Preuve réelle** : ≥ 1 recherche Brave bornée + dossier.

### LOT 9 — SOCIAL

- **Objectif** : préparer la publication du jour.
- **Périmètre** : idées, variantes distinctes, version choisie, calendrier ; **export/copier manuel** (accepté V1) ; publication native **optionnelle** si API réelle prouvée.
- **GO publication** (si native) : payload versionné/hash ; sinon statut « prêt à publier manuellement » — jamais de faux succès.
- **Exclusions** : faux succès ; fixtures seules comme preuve d’un connecteur natif.
- **Mémoire/budget** : historique par projet ; IA bornée sur budget commun.
- **Acceptation** : variantes non clones ; export utilisable.
- **Démo** : 2 variantes → export. Preuve native seulement si API validée.

### LOT 10 — Sauvegarde, restauration, résolution comptable, installation

- **Objectif** : ne pas perdre l’état ; clore les incertitudes budgétaires avec **preuves**.
- **Backup** : ensemble cohérent = **SQLite + artefacts privés** (dont contenus des snapshots code).
- **Restore** : dans un **`data_dir` distinct et isolé** — **sans** effacer les données quotidiennes.
- **Secrets** : exclus du backup versionné / non exportés en clair ; procédure documentée (références credentials, pas les secrets).
- **Exécutions interrompues restaurées** : après restore, même logique que reconcile LOT 5 (`interrupted` / `blocked_uncertain`) ; pas de reprise LLM automatique ; réserves ambiguës conservées jusqu’à résolution.
- **Résolution comptable** (report LOT 5) : workflow distinct de l’ack humain ; preuves (export usage / facture / note) ; historique ; passage incertain → confirmé ou soldé documenté ; **aucun** « pris en compte » seul.
- **Exclusions** : cloud sync ; multi-machine magique.
- **Acceptation** : backup → restore isolé → projets/revues/snapshots/budgets OK ; ≥ 1 résolution d’incertain avec preuve.
- **Démo** : cycle sur machine locale.

### LOT 11 — Stabilisation et démonstration publique V1

- **Objectif** : dépôt public démontrable ; gate V1.
- **Périmètre** :
  - installation **neuve en démo** (fixtures) bout-en-bout ;
  - **relecture** des parcours réels déjà validés (TECH, MAIL, SALES, SOCIAL) **sans répéter inutilement** les appels payants (captures, journaux, checklist) ;
  - limites restantes documentées ;
  - **procédure quotidienne de démarrage** (README) ;
  - audit consultable ; licence/nom si Jérôme tranche.
- **Exclusions** : données personnelles ; secrets ; V2/V3 ; re-smoke payant systématique.
- **Acceptation** : checklist §8 ; clone neuf démo OK ; preuves réels archivées sans nouveaux débits inutiles.
- **Démo** : script/doc de reproduction publique.

## 7. Tableau synthétique

| # | Statut | Thème |
|---:|---|---|
| 0–4 | Validés | Fondation → code (HQ + portraits inclus) |
| 5 | GO | Durabilité / events / SSE |
| 6 | À valider | Cursor / GO hash / export |
| 7 | À valider | MAIL réel + GO envoi |
| 8 | À valider | SALES + Brave Search (proposé) |
| 9 | À valider | SOCIAL export (+ native opt.) |
| 10 | À valider | Backup/restore + résolution comptable |
| 11 | À valider | Gate V1 + démarrage quotidien |

**Total de référence : 12 lots (0–11).**

## 8. Définition vérifiable « V1 terminée »

Cocher dans `docs/slices/v1-gate.md` (créé au LOT 11) :

- [ ] HQ + portraits ; TECH démo + réel durable
- [ ] Décision TECH ≠ GO Cursor ≠ GO envoi/publication ; hash respectés
- [ ] MAIL réel + mode fichier démo (fixtures ≠ preuve réelle)
- [ ] SALES sourcé (Brave ou équivalent GO) + relais MAIL
- [ ] SOCIAL exportable ; native seulement si prouvée
- [ ] Mémoire isolée par projet ; budget commun ; audit consultable
- [ ] Résolution comptable des incertains avec preuves
- [ ] Backup/restore isolé (SQLite + snapshots) ; secrets hors backup
- [ ] Install neuve démo + preuves réels sans débits inutiles
- [ ] Procédure quotidienne + limites documentées
- [ ] Aucun item V2/V3 requis (pas de QG animé)

## 9. Prochaines étapes

1. ~~Valider la roadmap~~ — **fait**.
2. Terminer / valider le **LOT 5** (GO acquis).
3. Aucun lot ≥ 6 sans **nouveau GO** explicite.
