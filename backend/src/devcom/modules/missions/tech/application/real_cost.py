from __future__ import annotations

from datetime import datetime
from typing import Any

from devcom.modules.billing.adapters.rate_tables import FxTable, OpenAiRateTable
from devcom.modules.billing.adapters.sqlalchemy_ledger import SqlAlchemyBudgetLedger
from devcom.modules.billing.domain.money import (
    eur_micros_from_usd_micros,
    usd_micros_from_tokens,
)
from devcom.modules.missions.tech.ports.llm_completion import LlmResult, LlmUsage


def record_step_cost(
    *,
    ledger: SqlAlchemyBudgetLedger,
    rates: OpenAiRateTable,
    fx: FxTable,
    regional: str,
    review_id: str,
    step: dict[str, Any],
    result: LlmResult,
    now: datetime,
) -> None:
    if result.usage is None:
        _write(ledger, review_id, step, None, 0, 0, "uncertain", "unknown", now)
        return
    usd, eur = _priced(rates, fx, regional, step["model_id"], result.usage)
    _write(
        ledger,
        review_id,
        step,
        result.usage,
        usd,
        eur,
        "confirmed",
        "ok" if result.ok else "invalid",
        now,
    )


def _priced(
    rates: OpenAiRateTable,
    fx: FxTable,
    regional: str,
    model_id: str,
    usage: LlmUsage,
) -> tuple[int, int]:
    model = rates.models[model_id]
    usd = usd_micros_from_tokens(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        input_usd_per_mtok=model.input_uncached,
        output_usd_per_mtok=model.output,
        uplift_ratio=regional,
    )
    eur = eur_micros_from_usd_micros(
        usd, usd_to_eur=fx.rate, fx_margin_ratio=fx.fx_margin_ratio
    )
    return usd, eur


def _write(
    ledger: SqlAlchemyBudgetLedger,
    review_id: str,
    step: dict[str, Any],
    usage: LlmUsage | None,
    usd: int,
    eur: int,
    cost_status: str,
    result_status: str,
    now: datetime,
) -> None:
    ledger.record_usage(
        review_id=review_id,
        step_key=step["step_key"],
        provider="openai",
        model_id=step["model_id"],
        input_tokens=0 if usage is None else usage.input_tokens,
        output_tokens=0 if usage is None else usage.output_tokens,
        reasoning_tokens=0 if usage is None else usage.reasoning_tokens,
        usd_micros=usd,
        eur_micros=eur,
        cost_status=cost_status,
        result_status=result_status,
        now=now,
    )
