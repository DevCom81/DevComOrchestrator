# Assets DevCom HQ

## Référence visuelle

- `Tableau de bord DevCom HQ.png` — mockup de référence pour reconstruire le HQ (marine / crème / turquoise, sidebar, en-tête, grille d’agents, panneaux bas).

Les noms `dashboard.png` ne sont pas utilisés ; la référence canonique est le fichier ci-dessus.

## Personnages agents (PNG RGBA 1254×1254)

Conserver ces originaux inchangés. L’application utilise des **copies renommées** dans `frontend/public/agents/`.

| Agent (ARCHITECTURE.md) | Fichier original | Copie frontend |
|---|---|---|
| Architecte | `Architecte stylisé avec plans bleus.png` | `architecte.png` |
| Cyber | `Héroïne cyber au bouclier verrouillé.png` | `cyber.png` |
| QA | `Personnage QA souriant, porte-bloc et pouce levé.png` | `qa.png` |
| DevOps | `Personnage DevOps en orange avec tablette-2.png` | `devops.png` |
| FullStack | `Développeuse stylisée sur cube avec laptop-3.png` | `fullstack.png` |
| SQL / Data | `Homme SQL aux bases empilées-4.png` | `sql_data.png` |
| Synthétiseur TECH | `Synthétiseuse en tailleur crème, cartes bleues-5.png` | `synthetiseur_tech.png` |
| Vendeur | `Vendeur souriant en blazer corail-6.png` | `vendeur.png` |
| Secrétaire | `Secrétaire au cardigan doré, carnet et enveloppe-7.png` | `secretaire.png` |
| Social | `Héroïne rose au mégaphone-8.png` | `social.png` |
| Dispatcher | `Dispatcher stylisé pointant avec sa tablette-9.png` | `dispatcher.png` |

## Règles d’intégration UI

1. Afficher les PNG avec `object-fit: contain` — **pas** d’étirement ni de rognage.
2. Les chemins d’images et tokens de couleur vivent dans le **mapping de présentation frontend** (`agentPresentation.ts`), pas dans le domaine Python.
3. Les spécialités affichées viennent du catalogue `contracts/agents/catalogue.json` (aligné ARCHITECTURE.md), pas du texte marketing du mockup.
4. En lot 0, chaque carte affiche **Non activé** — aucun faux état opérationnel.
5. Ne pas committer de retouche destructive des originaux ; régénérer les copies si besoin.
