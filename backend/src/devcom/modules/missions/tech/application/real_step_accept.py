from __future__ import annotations

from collections.abc import Callable
from typing import Any

from devcom.modules.missions.tech.adapters.sqlalchemy_steps import SqlAlchemyStepStore
from devcom.modules.missions.tech.application.real_ingest import (
    ingest_analysis,
    ingest_critique,
    ingest_reply,
)
from devcom.modules.missions.tech.domain.artifacts import (
    Challenge,
    ContextSnapshot,
    Finding,
    SpecialistAnalysis,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import TechReviewStatus
from devcom.modules.missions.tech.ports.llm_completion import LlmCompletionPort, LlmResult


def accept_input_bound(
    *,
    llm: LlmCompletionPort,
    steps: SqlAlchemyStepStore,
    review: TechReview,
    step_key: str,
    request: Any,
    fail: Callable[[TechReview, str, TechReviewStatus], None],
) -> bool:
    counted, method = llm.count_input_tokens(request)
    unreliable = counted is None or method.endswith("non_guaranteed")
    if unreliable or counted > request.max_input_tokens:
        message = (
            f"input bound refused ({method})"
            if unreliable
            else f"input tokens {counted} > {request.max_input_tokens}"
        )
        steps.mark(review.id, step_key, status="failed", error_message=message)
        reason = (
            "input token count unreliable — refused without silent truncate"
            if unreliable
            else "input exceeds bound"
        )
        fail(review, reason, TechReviewStatus.FAILED_PARTIAL)
        return False
    return True


def accept_result(
    *,
    steps: SqlAlchemyStepStore,
    review: TechReview,
    step: dict[str, Any],
    result: LlmResult,
    analyses: dict[str, SpecialistAnalysis],
    findings: dict[str, Finding],
    challenges: list[Challenge],
    fail: Callable[[TechReview, str, TechReviewStatus], None],
) -> bool:
    step_key = step["step_key"]
    if not result.ok or result.parsed is None:
        steps.mark(
            review.id,
            step_key,
            status="failed",
            error_message=result.error_message or result.error_code,
            cost_status="confirmed" if result.usage else "uncertain",
        )
        fail(
            review,
            result.error_message or "provider/result failure",
            TechReviewStatus.FAILED_PARTIAL,
        )
        return False
    if not ingest_parsed(step, result.parsed, analyses, findings, challenges, review.snapshot):
        steps.mark(
            review.id,
            step_key,
            status="failed",
            result=result.parsed,
            error_message="invalid references or contract",
            cost_status="confirmed",
        )
        fail(review, "invalid structured result", TechReviewStatus.FAILED_PARTIAL)
        return False
    steps.mark(
        review.id, step_key, status="completed", result=result.parsed, cost_status="confirmed"
    )
    return True


def ingest_parsed(
    step: dict[str, Any],
    parsed: dict[str, Any],
    analyses: dict[str, SpecialistAnalysis],
    findings: dict[str, Finding],
    challenges: list[Challenge],
    snapshot: ContextSnapshot | None,
) -> bool:
    allowed_refs = {"snapshot:project"}
    if snapshot is not None:
        allowed_refs.add(f"snapshot:{snapshot.project_id}")
    phase = step["phase"]
    if phase == "analyze":
        return ingest_analysis(step, parsed, analyses, findings, allowed_refs)
    if phase == "critique":
        return ingest_critique(step, parsed, findings, challenges, allowed_refs)
    if phase == "reply":
        return ingest_reply(step, parsed, analyses, findings, challenges)
    return True
