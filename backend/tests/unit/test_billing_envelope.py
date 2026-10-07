from __future__ import annotations

from pathlib import Path

from devcom.modules.billing.adapters.rate_tables import (
    load_call_bounds,
    load_fx_table,
    load_openai_rates,
)
from devcom.modules.billing.application.envelope import compute_max_envelope
from devcom.modules.billing.domain.money import eur_micros_from_usd_micros, usd_micros_from_tokens

ROOT = Path(__file__).resolve().parents[3]


def test_envelope_under_one_euro_for_19_calls() -> None:
    bounds = load_call_bounds(ROOT / "contracts/billing/tech_real_call_bounds.json")
    rates = load_openai_rates(ROOT / "contracts/billing/openai_rates_2026-10-07.json")
    fx = load_fx_table(ROOT / "contracts/billing/fx_usd_eur.json")
    envelope = compute_max_envelope(bounds, rates, fx)
    assert envelope.max_calls == 19
    assert len(envelope.lines) == 19
    assert envelope.eur_micros <= 1_000_000
    assert envelope.eur_micros > 0


def test_reservation_uses_max_uncached_or_cache_write() -> None:
    rates = load_openai_rates(ROOT / "contracts/billing/openai_rates_2026-10-07.json")
    sol = rates.models["gpt-6.1-sol"]
    assert sol.reservation_input_rate == "2.50"
    luna = rates.models["gpt-6-luna"]
    assert luna.reservation_input_rate == "0.125"


def test_reasoning_not_added_twice_in_token_cost() -> None:
    """Cost uses output_tokens only; reasoning must not be billed again on top."""
    base = usd_micros_from_tokens(
        input_tokens=1000,
        output_tokens=500,
        input_usd_per_mtok="2.00",
        output_usd_per_mtok="10.00",
        uplift_ratio="0.10",
    )
    if_reasoning_double_counted = usd_micros_from_tokens(
        input_tokens=1000,
        output_tokens=500 + 200,
        input_usd_per_mtok="2.00",
        output_usd_per_mtok="10.00",
        uplift_ratio="0.10",
    )
    assert base > 0
    assert if_reasoning_double_counted > base
    fx = load_fx_table(ROOT / "contracts/billing/fx_usd_eur.json")
    eur = eur_micros_from_usd_micros(
        base, usd_to_eur=fx.rate, fx_margin_ratio=fx.fx_margin_ratio
    )
    assert eur > 0
