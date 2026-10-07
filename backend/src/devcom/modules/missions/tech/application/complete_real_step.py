from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.billing.adapters.rate_tables import FxTable, OpenAiRateTable
from devcom.modules.billing.domain.money import (
    eur_micros_from_usd_micros,
    usd_micros_from_tokens,
)
from devcom.modules.missions.tech.adapters.sqlalchemy_events import SqlAlchemyEventStore
from devcom.modules.missions.tech.application.persist_step_outcome import persist_step_outcome
from devcom.modules.missions.tech.application.real_step_accept import ingest_parsed
from devcom.modules.missions.tech.domain.artifacts import (
    Challenge,
    Finding,
    SpecialistAnalysis,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import TechReviewStatus
from devcom.modules.missions.tech.ports.llm_completion import LlmResult
from devcom.modules.projects.domain.code_artifacts import CodeSnapshot


def complete_real_step(
    *,
    sessions: sessionmaker[Session],
    events: SqlAlchemyEventStore,
    rates: OpenAiRateTable,
    fx: FxTable,
    regional: str,
    review: TechReview,
    step: dict[str, Any],
    result: LlmResult,
    analyses: dict[str, SpecialistAnalysis],
    findings: dict[str, Finding],
    challenges: list[Challenge],
    code_snapshot: CodeSnapshot | None,
    now: datetime,
) -> tuple[bool, TechReviewStatus | None, str | None]:
    """Persist step+usage+events atomically. Returns (ok, fail_status, message)."""
    usd, eur, cost_status, result_status = _cost(rates, fx, regional, step, result)
    if not result.ok or result.parsed is None:
        persist_step_outcome(
            sessions=sessions,
            events=events,
            review_id=review.id,
            step=step,
            status="failed",
            result=None,
            error_message=result.error_message or result.error_code,
            cost_status=cost_status,
            result_status=result_status,
            usage=_usage_dict(result),
            usd_micros=usd,
            eur_micros=eur,
            provider="openai",
            model_id=step["model_id"],
            now=now,
        )
        if cost_status == "uncertain":
            return False, TechReviewStatus.BLOCKED_UNCERTAIN, "uncertain provider cost/result"
        return False, TechReviewStatus.FAILED_PARTIAL, result.error_message or "provider failure"
    if not ingest_parsed(
        step,
        result.parsed,
        analyses,
        findings,
        challenges,
        review.snapshot,
        code_snapshot=code_snapshot,
    ):
        persist_step_outcome(
            sessions=sessions,
            events=events,
            review_id=review.id,
            step=step,
            status="failed",
            result=result.parsed,
            error_message="invalid references or contract",
            cost_status=cost_status,
            result_status="invalid",
            usage=_usage_dict(result),
            usd_micros=usd,
            eur_micros=eur,
            provider="openai",
            model_id=step["model_id"],
            now=now,
        )
        return False, TechReviewStatus.FAILED_PARTIAL, "invalid structured result"
    persist_step_outcome(
        sessions=sessions,
        events=events,
        review_id=review.id,
        step=step,
        status="completed",
        result=result.parsed,
        error_message=None,
        cost_status=cost_status,
        result_status=result_status,
        usage=_usage_dict(result),
        usd_micros=usd,
        eur_micros=eur,
        provider="openai",
        model_id=step["model_id"],
        now=now,
    )
    return True, None, None


def _usage_dict(result: LlmResult) -> dict[str, int] | None:
    if result.usage is None:
        return None
    return {
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
        "reasoning_tokens": result.usage.reasoning_tokens,
    }


def _cost(
    rates: OpenAiRateTable,
    fx: FxTable,
    regional: str,
    step: dict[str, Any],
    result: LlmResult,
) -> tuple[int, int, str, str]:
    if result.usage is None:
        return 0, 0, "uncertain", "unknown"
    model = rates.models[step["model_id"]]
    usd = usd_micros_from_tokens(
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
        input_usd_per_mtok=model.input_uncached,
        output_usd_per_mtok=model.output,
        uplift_ratio=regional,
    )
    eur = eur_micros_from_usd_micros(
        usd, usd_to_eur=fx.rate, fx_margin_ratio=fx.fx_margin_ratio
    )
    return usd, eur, "confirmed", "ok" if result.ok else "invalid"
