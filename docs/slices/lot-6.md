# LOT 6 — Plan Cursor, GO, export, retour (fondation)

## Statut

Fondation **livrée** — acquis conservés. Validation manuelle backend/frontend
selon commandes ci-dessous. Compléments : **LOT 6A** (preuve SDK), **LOT 6B**
(adapter) — voir slices dédiées. Manuel = dépannage une fois 6B livré.

## Objectif

Depuis une décision TECH, préparer un paquet Cursor versionné, l’approuver
par GO distinct (hash), l’exporter, importer rapport/diff, vérifier
structurellement, et optionnellement créer une revue TECH du retour **sans run**.

## Critères

- [ ] Plan lié revue/décision/ADR/snapshot (snapshot optionnel → base inconnue)
- [ ] Preview ≡ contenu approuvé (markdown + manifeste, hash non autoréférentiel)
- [ ] GO ≠ décision TECH ; édition invalide le GO ; TTL 24 h
- [ ] Export + consommation GO atomiques ; replay idempotency ; retéléchargement OK
- [ ] Expiration bloque nouvel export, pas l’accès à un export existant
- [ ] Retours multiples liés à `export_id` ; declared_* ≠ preuve
- [ ] Diff hostile / chemins refusés ; vérif en mémoire
- [ ] Contexte immuable rapport+diff ; créer revue sans LLM implicite
- [ ] Module `approvals` mince réutilisable

## Exclusions

Agent Cursor auto (→ 6A/6B), apply patch, push, LOT 7+.

## Commandes de validation (groupées)

```bash
# 1) Backend
cd /home/jey/Projets/MyProjects/DevComOrchestrator/backend
export PYTHONPATH=src
alembic upgrade head
ruff check src tests
mypy src
pytest -q tests/integration/test_cursor_lot6.py \
  tests/integration/test_tech_api_flow.py \
  tests/integration/test_tech_durability.py \
  tests/integration/test_tech_real_pipeline.py
```

```bash
# 2) Frontend
cd /home/jey/Projets/MyProjects/DevComOrchestrator/frontend
npm run lint
npm run test -- --run
npm run build
```

```bash
# 3) App (FakeLlm)
# A
cd /home/jey/Projets/MyProjects/DevComOrchestrator/backend
export PYTHONPATH=src DEVCOM_MODE=demo DEVCOM_LLM_ADAPTER=fake
uvicorn devcom.bootstrap.app_factory:create_app --factory --host 127.0.0.1 --port 8765
# B
cd /home/jey/Projets/MyProjects/DevComOrchestrator/frontend
npm run dev
```

## Parcours utilisateur

1. Revue démo → décider une proposition.
2. Préparer plan Cursor → éditer → aperçu (markdown + manifeste + hash).
3. Demander GO → accorder → créer export → retélécharger sans nouveau GO.
4. Modifier le plan → export refusé sans nouveau GO.
5. Importer rapport + diff → statut de vérification explicite (pas « tests OK »).
6. Prévisualiser contexte → « Créer revue TECH du retour » sans lancement auto.

## Décisions

ADR 0007 ; suite liaison : ADR 0008, lots 6A/6B.
