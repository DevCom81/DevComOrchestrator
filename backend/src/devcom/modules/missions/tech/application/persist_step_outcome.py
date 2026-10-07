from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.billing.adapters.sqlalchemy_ledger import _apply_cost_to_period
from devcom.modules.billing.adapters.sqlalchemy_models import (
    BudgetPeriodRow,
    BudgetReservationRow,
    UsageRecordRow,
)
from devcom.modules.missions.tech.adapters.sqlalchemy_events import SqlAlchemyEventStore
from devcom.modules.missions.tech.adapters.sqlalchemy_models import TechPipelineStepRow


def mark_step_started(
    *,
    sessions: sessionmaker[Session],
    events: SqlAlchemyEventStore,
    review_id: str,
    step_key: str,
    now: datetime,
) -> bool:
    """Persist in_flight + step.started BEFORE provider call (one transaction)."""
    with sessions() as session:
        row = _step(session, review_id, step_key)
        if row is None:
            return False
        if row.status in {"completed", "skipped", "failed", "uncertain"}:
            return False
        if row.status != "pending":
            return False
        row.status = "in_flight"
        events.append(
            review_id=review_id,
            event_type="step.started",
            dedupe_key=f"step.started:{step_key}",
            payload={"step_key": step_key},
            occurred_at=now,
            session=session,
        )
        session.commit()
        return True


def persist_step_outcome(
    *,
    sessions: sessionmaker[Session],
    events: SqlAlchemyEventStore,
    review_id: str,
    step: dict[str, Any],
    status: str,
    result: dict[str, Any] | None,
    error_message: str | None,
    cost_status: str,
    result_status: str,
    usage: dict[str, int] | None,
    usd_micros: int,
    eur_micros: int,
    provider: str,
    model_id: str,
    now: datetime,
) -> bool:
    """Atomically write step status + usage + events (provider call already done)."""
    step_key = step["step_key"]
    with sessions() as session:
        row = _step(session, review_id, step_key)
        if row is None or row.status in {"completed", "skipped", "failed", "uncertain"}:
            return False
        row.status = status
        if result is not None:
            row.result_json = json.dumps(result, ensure_ascii=False)
        if error_message is not None:
            row.error_message = error_message
        row.cost_status = cost_status
        reservation = session.scalars(
            select(BudgetReservationRow).where(BudgetReservationRow.review_id == review_id)
        ).first()
        if reservation is None:
            return False
        period = session.scalars(
            select(BudgetPeriodRow).where(BudgetPeriodRow.month_id == reservation.month_id)
        ).first()
        if period is None:
            return False
        session.add(
            UsageRecordRow(
                id=str(uuid4()),
                review_id=review_id,
                step_key=step_key,
                provider=provider,
                model_id=model_id,
                input_tokens=0 if usage is None else usage["input_tokens"],
                output_tokens=0 if usage is None else usage["output_tokens"],
                reasoning_tokens=0 if usage is None else usage["reasoning_tokens"],
                usd_micros=usd_micros,
                eur_micros=eur_micros,
                cost_status=cost_status,
                result_status=result_status,
                detail_json=None,
                created_at=now,
            )
        )
        _apply_cost_to_period(
            reservation, period, cost_status, usd_micros=usd_micros, eur_micros=eur_micros
        )
        event_type = "step.completed" if status == "completed" else "step.failed"
        events.append(
            review_id=review_id,
            event_type=event_type,
            dedupe_key=f"{event_type}:{step_key}",
            payload={
                "step_key": step_key,
                "cost_status": cost_status,
                "result_status": result_status,
                "eur_micros": eur_micros,
            },
            occurred_at=now,
            session=session,
        )
        events.append(
            review_id=review_id,
            event_type="budget.usage",
            dedupe_key=f"budget.usage:{step_key}",
            payload={
                "step_key": step_key,
                "cost_status": cost_status,
                "eur_micros": eur_micros,
            },
            occurred_at=now,
            session=session,
        )
        session.commit()
        return True


def _step(session: Session, review_id: str, step_key: str) -> TechPipelineStepRow | None:
    return session.scalars(
        select(TechPipelineStepRow).where(
            TechPipelineStepRow.review_id == review_id,
            TechPipelineStepRow.step_key == step_key,
        )
    ).first()
