# ADR 0007 — Plan Cursor, GO distinct, export et retour

## Statut

Accepté — LOT 6 (2026-10-07).

## Contexte

La décision TECH + ADR n’autorise pas l’implémentation. Il faut un paquet
exportable, un GO lié au hash exact, un export manuel, puis un import de
rapport/diff sans appliquer de patch ni croire les déclarations Cursor.

## Décision

- Module mince `approvals` (contrat commun) sans dépendance MAIL→TECH.
- Plan Cursor propriétaire de son paquet ; hash `cursor_package_canon_v1`
  non autoréférentiel.
- Grant/refuse GO = commandes de gouvernance (pas EXTERNAL récursif) ;
  l’export contrôle et consomme le GO.
- Export immuable + consommation GO atomiques ; retéléchargement sans nouveau GO ;
  expiration bloque un nouvel export, pas l’accès à un export existant.
- Retours multiples liés à un `export_id` ; vérification structurelle du diff
  vs snapshot en mémoire ; `declared_*` ≠ preuve.
- « Créer revue TECH du retour » avec contexte immuable (rapport+diff) ;
  aucun run automatique.

## Conséquences

UI post-`decided` ; migration `0007` ; permissions cursor.* ; tests doubles.
