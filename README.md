# DevCom Command Center

Application locale pour orchestrer des spécialistes IA sous contrôle humain.

**LOT 0** : fondation démo — HQ interactif, premier projet SQLite.  
**LOT 1** : Capability Registry, Permission Policy, Dispatcher démo déterministe, missions bornées (routage consultable, sans exécution IA).  
**LOT 2** : Revue TECH fictive (scénarios versionnés, propositions, blocage critique, ADR démo).

## Prérequis

- Python 3.12+
- Node.js 20+ (LTS recommandé)
- npm

## Configuration

Variables (voir `.env.example`) :

| Variable | Défaut | Rôle |
|---|---|---|
| `DEVCOM_MODE` | `demo` | Mode unique du lot 0 |
| `DEVCOM_HOST` | `127.0.0.1` | Bind API |
| `DEVCOM_PORT` | `8765` | Port API |
| `DEVCOM_DATA_DIR` | `~/.local/share/devcom/demo` | SQLite et données privées |
| `DEVCOM_CORS_ORIGINS` | origines Vite | CORS |
| `DEVCOM_ALLOWED_HOSTS` | `127.0.0.1:8765,localhost:8765` | Host mutations |

Les bases, logs et `.env` restent hors Git.

## Démarrage (résumé)

Les commandes exactes détaillées sont fournies dans le compte rendu de livraison du LOT 0.

1. Installer le backend (`pip install -e ".[dev]"`) et générer/vérifier le lock.
2. `alembic upgrade head`
3. Installer le frontend (`npm install`) — génère `package-lock.json`.
4. Dev : API uvicorn + `npm run dev` (proxy `/api`).
5. Prod locale : `npm run build` puis servir `frontend/dist` via FastAPI.

## Structure

Voir `ARCHITECTURE.md` et `docs/slices/lot-0.md`.
