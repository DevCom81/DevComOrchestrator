from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from devcom.modules.billing.adapters.rate_tables import FxTable, OpenAiRateTable
from devcom.modules.billing.domain.money import (
    eur_micros_from_usd_micros,
    usd_micros_from_tokens,
)

SPECIALISTS = (
    "architecte",
    "cyber",
    "qa",
    "devops",
    "fullstack",
    "sql_data",
)


@dataclass(frozen=True, slots=True)
class EnvelopeLine:
    step_key: str
    agent_id: str
    model_id: str
    max_input: int
    max_output: int
    usd_micros: int
    eur_micros: int


@dataclass(frozen=True, slots=True)
class ReviewEnvelope:
    lines: tuple[EnvelopeLine, ...]
    max_calls: int
    usd_micros: int
    eur_micros: int
    fx_rate: str
    fx_rate_date: str
    fx_margin_ratio: str
    rates_verified_at: str
    regional_uplift_ratio: str


def compute_max_envelope(
    bounds: dict[str, Any],
    rates: OpenAiRateTable,
    fx: FxTable,
    input_tokens_by_step: dict[str, int] | None = None,
) -> ReviewEnvelope:
    uplift = rates.regional_uplift_ratio if bounds.get("apply_regional_uplift") else "0"
    lines = (
        _phase_lines(
            "analyze", bounds, rates, fx, uplift, optional=False, inputs=input_tokens_by_step
        )
        + _phase_lines(
            "critique", bounds, rates, fx, uplift, optional=False, inputs=input_tokens_by_step
        )
        + _phase_lines(
            "reply", bounds, rates, fx, uplift, optional=True, inputs=input_tokens_by_step
        )
        + [_synth_line(bounds, rates, fx, uplift, inputs=input_tokens_by_step)]
    )
    return ReviewEnvelope(
        lines=tuple(lines),
        max_calls=int(bounds["max_calls"]),
        usd_micros=sum(item.usd_micros for item in lines),
        eur_micros=sum(item.eur_micros for item in lines),
        fx_rate=fx.rate,
        fx_rate_date=fx.rate_date,
        fx_margin_ratio=fx.fx_margin_ratio,
        rates_verified_at=rates.verified_at,
        regional_uplift_ratio=uplift,
    )


def _phase_lines(
    phase: str,
    bounds: dict[str, Any],
    rates: OpenAiRateTable,
    fx: FxTable,
    uplift: str,
    *,
    optional: bool,
    inputs: dict[str, int] | None,
) -> list[EnvelopeLine]:
    del optional  # reserved for documentation of optional reply phase
    models = bounds["models"]
    token_bounds = bounds["token_bounds"]
    lines: list[EnvelopeLine] = []
    for agent_id in SPECIALISTS:
        model_id = models[agent_id]["model"]
        key = f"{phase}_architecte" if agent_id == "architecte" else phase
        step_key = f"{phase}:{agent_id}"
        lines.append(
            _line(
                step_key,
                agent_id,
                model_id,
                token_bounds[key],
                rates,
                fx,
                uplift,
                input_override=None if inputs is None else inputs.get(step_key),
            )
        )
    return lines


def _synth_line(
    bounds: dict[str, Any],
    rates: OpenAiRateTable,
    fx: FxTable,
    uplift: str,
    *,
    inputs: dict[str, int] | None,
) -> EnvelopeLine:
    synth = bounds["models"]["synthetiseur_tech"]
    return _line(
        "synthesize",
        "synthetiseur_tech",
        synth["model"],
        bounds["token_bounds"]["synthesize"],
        rates,
        fx,
        uplift,
        input_override=None if inputs is None else inputs.get("synthesize"),
    )


def _line(
    step_key: str,
    agent_id: str,
    model_id: str,
    bounds: dict[str, Any],
    rates: OpenAiRateTable,
    fx: FxTable,
    uplift: str,
    *,
    input_override: int | None = None,
) -> EnvelopeLine:
    model = rates.models[model_id]
    max_input = int(bounds["max_input"])
    max_output = int(bounds["max_output"])
    input_tokens = max_input if input_override is None else input_override
    if input_tokens > max_input:
        raise ValueError(
            f"step {step_key} input upper bound {input_tokens} exceeds max_input {max_input}"
        )
    usd = usd_micros_from_tokens(
        input_tokens=input_tokens,
        output_tokens=max_output,
        input_usd_per_mtok=model.reservation_input_rate,
        output_usd_per_mtok=model.output,
        uplift_ratio=uplift,
    )
    eur = eur_micros_from_usd_micros(
        usd,
        usd_to_eur=fx.rate,
        fx_margin_ratio=fx.fx_margin_ratio,
    )
    return EnvelopeLine(
        step_key=step_key,
        agent_id=agent_id,
        model_id=model_id,
        max_input=max_input,
        max_output=max_output,
        usd_micros=usd,
        eur_micros=eur,
    )
