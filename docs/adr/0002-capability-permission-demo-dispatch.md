# ADR 0002 — Capacités, permissions et routage démo (LOT 1)

- Statut : accepté
- Date : 2026-10-07

## Contexte

Le LOT 1 doit router des missions bornées sans exécuter d’agents ni d’actions externes, tout en séparant clairement compétences et permissions.

## Décisions

1. **Capability Registry** (`contracts/capabilities/registry.json`) : qui peut traiter quelle tâche (`allowed_agents` / `excluded_agents`). Source unique ; pas de listes concurrentes côté code.
2. **Permission Policy** (`contracts/permissions/policy.json`) : effet `allow` / `deny` / `require_authorization` par `action_id`, refus par défaut si action inconnue. Les outils restent désactivés (`tools_enabled: false`).
3. Une compétence n’accorde aucune permission EXTERNAL.
4. **Dispatcher démo déterministe** (`contracts/dispatch/demo_rules.json`) : règles de phrases/groupes, clairement labellisé. Hors règles → clarification avec choix structurés (max 3).
5. **Intention EXTERNAL** (« Envoyer ce mail au client ») : bloque la mission avec le message `Autorisation requise — action à préciser`. Pas de `ApprovalRequest`, pas de `payload_hash`, pas de destinataire/contenu inventés. `ApprovalRequest` est réservé à une action concrète versionnée (lots ultérieurs). Aucun bouton d’approbation ni endpoint d’exécution en LOT 1.
6. Les versions de registry, policy et règles, ainsi que l’explication de routage, sont persistées avec chaque mission.
7. Missions lit l’existence projet via un **port minimal**, sans injection du repository interne `projects`.

## États mission retenus (LOT 1)

`draft` → `awaiting_clarification` | `routed` | `blocked_authorization`

Pas d’état `awaiting_approval` tant qu’aucune action concrète n’est versionnée.

## Conséquences

- Le parcours s’arrête au routage consultable (ou au blocage EXTERNAL).
- Le débat TECH et l’exécution d’avis restent au LOT 2.
