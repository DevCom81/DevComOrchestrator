# ADR 0001 — Fondation locale LOT 0

- Statut : accepté
- Date : 2026-10-07

## Contexte

Le LOT 0 doit livrer un Command Center local en mode démo : HQ visuel, CRUD projet persistant SQLite, sans missions ni fournisseurs.

## Décision

- Stack : Python 3.12+ / FastAPI / SQLAlchemy 2 / Alembic / SQLite ; React / TypeScript strict / Vite / TanStack Query.
- Mode : `demo` uniquement (`DEVCOM_MODE=demo`).
- Données : `~/.local/share/devcom/demo/` (override `DEVCOM_DATA_DIR`).
- API liée à `127.0.0.1:8765`.
- Catalogue agents : contrats JSON versionnés ; aucun état opérationnel dans le domaine.
- Présentation (PNG, accents CSS) : mapping frontend uniquement.
- UI : reconstruction du mockup `Assets/Tableau de bord DevCom HQ.png` avec états honnêtes (Non activé, Budget non activé, empty panels).

## Sécurité locale (LOT 0)

Protections mises en place :

1. Bind loopback explicite.
2. CORS limité aux origines Vite / app servie.
3. Middleware `LocalMutationGuard` sur `POST`/`PATCH`/`PUT`/`DELETE` sous `/api/` :
   - validation du header `Host` contre une allowlist ;
   - validation de `Origin` lorsqu’il est présent ;
   - exigence `Content-Type: application/json` ;
4. Aucune mutation via `GET`.
5. DTO Pydantic `extra=forbid`.

Limites documentées (non couvertes par ce lot) :

- Pas de session utilisateur ni CSRF cookie (API JSON sans cookie) : la défense repose sur Host/Origin + same-site navigateur.
- Une requête sans header `Origin` (ex. curl local) n’est pas rejetée pour Origin ; Host et JSON restent contrôlés.
- Pas de TLS local, pas de multi-utilisateur, pas de rate limiting.
- Le proxy Vite doit utiliser `changeOrigin: true` pour que `Host` cible le backend.

## Conséquences

- Base pour les lots suivants sans modules anticipés (missions, budget, SSE).
- Les lockfiles sont générés manuellement lors de l’installation initiale.
