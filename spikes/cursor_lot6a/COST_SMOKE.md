# Fiche coût — premier smoke Cursor (LOT 6A)

À lire **avant** `ALLOW_CURSOR_SMOKE=1` + `scripts/run_real_smoke.py`.
Un seul run micro, **sans retry automatique**.

Sources (2026-10-07) : docs SDK Python 1.0.36, Models & Pricing Cursor,
Usage limits, forum SDK (variant fast). **Aucun run agent exécuté** pour
remplir cette fiche. Liste des modèles du compte : script
`check_auth_and_models.py` (à lancer par Jérôme).

## Authentification

| Élément | État constaté (préparation agent) |
|---|---|
| Variable | `CURSOR_API_KEY` (user ou service-account ; Team Admin keys non supportées) |
| Présence | La variable peut être **définie** mais **refusée** par Cursor |
| Configuration | Dashboard → API Keys → User ou service-account key → `export CURSOR_API_KEY='…'` |
| Secrets | Ne jamais committer, logger, ni coller la clé dans le chat |

Sans clé : exit **3**. Clé invalide (`AuthenticationError`) : exit **6** —
ne pas contourner ; régénérer la clé et relancer `check_auth_and_models.py`.
Constat smoke préparatoire : `Invalid User API Key` tant que la clé valide
n’est pas exportée correctement.

## Modèle proposé

- Identifiant : **`composer-2.5`**
- Paramètre : **`fast=false`** (standard) — sans ce paramètre, l’API peut
  résoudre la variante **fast** (plus chère) tout en affichant l’id `composer-2.5`.
- Source : exemples docs SDK + retour forum Cursor SDK billing.
- Vérification compte : `python scripts/check_auth_and_models.py`
  (doit afficher `proposed_available: True`).
- Date de rédaction fiche : **2026-10-07**

Tarifs catalogue Cursor Models (par million de tokens, doc pricing) :

| Variante | Input | Cache read | Output |
|---|---:|---:|---:|
| Composer 2.5 (standard) | $0.50 | $0.20 | $2.50 |
| Composer 2.5 (Fast) | $3.00 | $0.50 | $15.00 |

Le smoke force **standard** pour limiter le coût unitaire.

## Facturation

- Les runs SDK suivent la **même grille / pools / Privacy Mode** que l’IDE.
- Dépense visible sous le tag **SDK** du usage dashboard.
- Pools : « Cursor Models » (Composer 2.5, …) vs « Other Models ».
- Si l’usage inclus reste : `charged_cents` peut être **0** (inclus plan / crédit).
- Si on-demand activé et pool épuisé : facturation au tarif API — **non plafonnée par ce script**.
- `agent.get_usage()` : coût serveur, éventuellement retardé ; pour agents
  **locaux**, peut renvoyer `feature_unavailable` selon le compte → alors
  se fier à `run.usage` + dashboard.

## Plafond réellement disponible

| Mécanisme | Disponible pour ce spike ? | Valeur / limite |
|---|---|---|
| Plafond budget DevCom (µEUR) | **Non** (hors moteur) | — |
| Plafond compte Cursor (pool inclus + Spending) | **Oui, côté compte** | À lire sur Dashboard → Spending **avant** le run |
| Kill-switch on-demand Cursor | **Oui si désactivé** dans le compte | Recommandé : on-demand **OFF** pour ce smoke |
| Timeout processus local | Opérationnel seulement | 300 s suggéré — **≠ garantie €** |
| Retry automatique | **Non** (interdit dans le code) | 0 |
| Garantie financière SDK | **Non** | Le SDK ne expose pas de hard cap € par run |

## Coût maximal garanti

- **Montant max garanti par ce dépôt / ce script : aucun.**
- Limite de la « garantie » : seule une combinaison **pool inclus restant +
  on-demand désactivé** sur le compte Cursor peut empêcher un débit hors forfait ;
  ce n’est **pas** contrôlé par DevCom. Un timeout tue le process, pas la facture
  déjà engagée.
- Estimation qualitative (non garantie) : micro-tâche 2 fichiers, modèle
  standard — typiquement une fraction du pool Cursor Models ; **vérifier
  Spending** avant de lancer.

Si le coût ne peut pas être borné sur le compte (on-demand ON + pool bas) :
**ne pas lancer** tant que Spending / on-demand n’est pas ajusté.

## Prérequis plan

- Doc Cursor : le plan **Start** n’inclut **pas** le Cursor SDK → upgrade
  Pro (ou équivalent avec SDK) requis.
- Privacy Mode : mêmes règles que l’IDE.

## Périmètre concret du run

- Worktree : `spikes/cursor_lot6a/worktrees/smoke-1/` (clone local neuf)
- Artefacts : `spikes/cursor_lot6a/artifacts/smoke-1/` (gitignorés)
- Tâche : implémenter `greet` selon `PACKAGE.md`
- Fichiers cibles : `hello.py`, `test_hello.py`
- Runtime : **local** ; `SandboxOptions(enabled=True)` ; `setting_sources=project`
- Env : scrub `DEVCOM_*` / clés LLM backend ; `CURSOR_API_KEY` conservée pour le SDK
- Push : non
- Send : **1** ; retry : **0**

## Décision

- [ ] Clé API exportée dans le shell (non commitée)
- [ ] `check_auth_and_models.py` → `proposed_available: True`
- [ ] Spending consulté ; on-demand OFF recommandé
- [ ] Jérôme autorise **ce** smoke unique
- Date / initiales : __________
