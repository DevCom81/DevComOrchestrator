# LOT 3 — Enveloppe réservée (recalcul 19 appels)

Vérifié le **2026-10-07**.

## Tarifs OpenAI Standard short context

| Modèle | Uncached in | Cache write | Output |
|---|---:|---:|---:|
| `gpt-6-luna` | $0.10 / MTok | $0.125 / MTok | $0.50 / MTok |
| `gpt-6.1-sol` | $2.00 / MTok | $2.50 / MTok | $10.00 / MTok |

Réservation entrée = **max(uncached, cache_write)** (jamais un hit cache pour autoriser).  
Majoration régionale **+10 %** appliquée à l’enveloppe.  
Raisonnement inclus dans `max_output` / `output_tokens` (pas de double compte).

## FX

- Source Frankfurter/ECB, date taux **2026-10-06** : `1 USD = 0.88739 EUR`
- **Re-vérifié le 2026-10-07** (`https://api.frankfurter.app/latest?from=USD&to=EUR`) — même taux.
- Marge FX **+5 %** → taux effectif `0.9317595`
- Calcul rationnel/décimal puis **ceil** vers micro-euros (`1 EUR = 1_000_000 µ€`)
- USD et EUR conservés séparément dans le ledger

## Comptage d’entrée

- Payload complet : system + user JSON + schéma Structured Outputs (+ reasoning effort).
- Méthode garantie : `POST /v1/responses/input_tokens` (SDK `inputTokens.count` si présent, sinon HTTP direct) — label `openai_responses_input_tokens`.
- Estimation `char/4` labellée `*_non_guaranteed` → **refus** (pas de borne présentée comme garantie, pas de troncature).
- FakeLlm (tests) : `fake_char_div4` déterministe.

## Graphe max 19 appels

4 × Sol (analyse + critique + réponse Architecte + synthèse) + 15 × Luna (5 spécialistes × analyse/critique/réponse).

## USD max (avant régional)

Bornes LOT 3 après marge critique/reply/synthèse (raisonnement + JSON Structured Outputs) :  
Après régional ×1.10 → **≈ $0.23925**  
EUR réservé ≈ **0.2229 €** ≈ **222 935 µ€** (calcul runtime ceil) (< plafond revue **1 000 000 µ€**).

Si un recalcul runtime dépasse 1 € → **refus de lancement** explicite.
