# LOT 5 — Durabilité TECH, événements, SSE

## Statut

Implémenté — en attente de validation manuelle (doubles uniquement).  
Roadmap V1 : trajectoire de référence validée ; résolution comptable reportée au **LOT 10**.

## Objectif

Retrouver une revue après navigation/fermeture d’onglet ou redémarrage backend,
sans faux « en cours » et sans nouvel appel LLM.

## Critères d’acceptation

- [ ] `interrupted` vs `blocked_uncertain` distincts
- [ ] Reconcile boot : plus de `running` orphelin ; idempotent
- [ ] `in_flight` avant appel ; complétion atomique résultat+usage+événement
- [ ] Budget : libération prouvée seulement ; réserve ambiguë conservée
- [ ] Acknowledge humain (motif+date) sans libérer réserve ambiguë ni confirmer coût
- [ ] SSE + events HTTP + polling secours ; 0 LLM sur GET/SSE/refresh
- [ ] UI : timeline, bannières, résultats partiels, liste revues sur Projet
- [ ] Snapshots LOT 4 et isolation démo/réel conservés

## Exclusions

Retry LLM, reprise auto, worker distribué, **résolution comptable fournisseur (LOT 10)**, LOT 6+.

## Décisions

ADR 0006, `contracts/tech/events_v1.json`, `docs/ROADMAP_V1.md`.

## Commandes de validation (manuel, groupées)

Prérequis : venv backend + deps frontend déjà installés. **Aucun appel OpenAI payant.**

```bash
# ——— 1) Backend ———
cd /home/jey/Projets/MyProjects/DevComOrchestrator/backend
export PYTHONPATH=src
alembic upgrade head
ruff check src tests
mypy src
pytest -q tests/integration/test_tech_durability.py \
  tests/integration/test_tech_real_pipeline.py \
  tests/integration/test_tech_api_flow.py \
  tests/integration/test_code_context.py
```

Attendu : migration `0006` OK ; ruff/mypy verts ; pytest verts
(interrupted ≠ blocked_uncertain ; ack sans libération ; events ; 0 LLM sur GET).

```bash
# ——— 2) Frontend ———
cd /home/jey/Projets/MyProjects/DevComOrchestrator/frontend
npm run lint
npm run test -- --run
npm run build
```

Attendu : lint/tests/build OK (dont `techStatus.test.tsx`).

```bash
# ——— 3) App locale (deux terminaux) ———
# Terminal A
cd /home/jey/Projets/MyProjects/DevComOrchestrator/backend
export PYTHONPATH=src DEVCOM_MODE=real DEVCOM_LLM_ADAPTER=fake
uvicorn devcom.bootstrap.app_factory:create_app --factory --host 127.0.0.1 --port 8765

# Terminal B
cd /home/jey/Projets/MyProjects/DevComOrchestrator/frontend
npm run dev
```

## Parcours utilisateur

1. Projet → liste « Revues TECH ».
2. Créer/lancer une revue réelle (fake) ; journal d’événements.
3. Redémarrage sous `running` → `interrupted` ou `blocked_uncertain` (pas orphelin).
4. Sur `blocked_uncertain` : « Pris en compte » → date/motif ; réserve toujours held ;
   message clair (pas de retry auto ; ack ≠ preuve fournisseur).
5. Résultats partiels visibles si analyses/usage déjà présents.
6. Quitter/revenir : état, steps, usage, sources LOT 4 conservés ; 0 nouvel appel LLM.

## Fichiers principaux

Backend : events, reconcile, persist atomique, SSE (`tech_events`), ack.  
Frontend : `EventTimeline`, `AcknowledgeUncertaintyPanel`, `PartialResultsNotice`,
`ProjectReviewsPanel`, `useReviewEvents`.  
Docs : ADR 0006, ROADMAP_V1, migration `0006_tech_events`.
