from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.billing.adapters.sqlalchemy_ledger import SqlAlchemyBudgetLedger
from devcom.modules.missions.tech.adapters.sqlalchemy_events import SqlAlchemyEventStore
from devcom.modules.missions.tech.adapters.sqlalchemy_models import TechReviewRow
from devcom.modules.missions.tech.adapters.sqlalchemy_steps import SqlAlchemyStepStore
from devcom.modules.missions.tech.domain.status import ExecutionMode, TechReviewStatus
from devcom.shared.time import Clock


def reconcile_interrupted_real_pipeline(
    *,
    session_factory: sessionmaker[Session],
    steps: SqlAlchemyStepStore,
    ledger: SqlAlchemyBudgetLedger,
    events: SqlAlchemyEventStore,
    clock: Clock,
) -> int:
    """Idempotent boot reconcile — no LLM, no double release, no duplicate events."""
    marked = steps.mark_in_flight_uncertain()
    ledger.clear_stale_lock()
    now = clock.now()
    _emit_uncertain_steps(events, steps, now)
    touched = 0
    with session_factory() as session:
        rows = session.scalars(
            select(TechReviewRow).where(
                TechReviewRow.execution_mode == ExecutionMode.REAL.value,
                TechReviewRow.status == TechReviewStatus.RUNNING.value,
            )
        ).all()
        for row in rows:
            touched += 1
            _reconcile_one(session, steps, ledger, events, row, now)
        session.commit()
    return marked + touched


def _emit_uncertain_steps(
    events: SqlAlchemyEventStore,
    steps: SqlAlchemyStepStore,
    now: datetime,
) -> None:
    for review_id, step_key in steps.list_uncertain_keys():
        events.append(
            review_id=review_id,
            event_type="step.uncertain",
            dedupe_key=f"step.uncertain:{step_key}",
            payload={"step_key": step_key},
            occurred_at=now,
        )


def _reconcile_one(
    session: Session,
    steps: SqlAlchemyStepStore,
    ledger: SqlAlchemyBudgetLedger,
    events: SqlAlchemyEventStore,
    row: TechReviewRow,
    now: datetime,
) -> None:
    step_rows = steps.list_steps(row.id)
    statuses = {item["status"] for item in step_rows}
    has_uncertain = "uncertain" in statuses
    has_started = bool(statuses & {"completed", "failed", "skipped", "uncertain", "in_flight"})
    if has_uncertain:
        _block_uncertain(session, events, row, now)
        return
    row.status = TechReviewStatus.INTERRUPTED.value
    if not has_started:
        row.failure_message = "interrupted before any provider call started"
        ledger.release_unused_envelope(row.id)
        events.append(
            review_id=row.id,
            event_type="budget.settled",
            dedupe_key="reconcile:settled_before_calls",
            payload={"reason": "no_call_started"},
            occurred_at=now,
            session=session,
        )
    else:
        row.failure_message = (
            "interrupted between steps — confirmed costs kept; "
            "unused reservation for non-started calls released"
        )
        ledger.release_unused_envelope(row.id)
        events.append(
            review_id=row.id,
            event_type="budget.settled",
            dedupe_key="reconcile:settled_between_steps",
            payload={"reason": "non_started_calls_released"},
            occurred_at=now,
            session=session,
        )
    events.append(
        review_id=row.id,
        event_type="review.interrupted",
        dedupe_key="reconcile:interrupted",
        payload={"has_started": has_started},
        occurred_at=now,
        session=session,
    )
    row.updated_at = now


def _block_uncertain(
    session: Session,
    events: SqlAlchemyEventStore,
    row: TechReviewRow,
    now: datetime,
) -> None:
    # Keep ambiguous reservation — never infer "no billing" from missing result.
    row.status = TechReviewStatus.BLOCKED_UNCERTAIN.value
    row.failure_message = (
        "interrupted with at least one uncertain call/cost — "
        "no automatic replay; provider billing may be unknown"
    )
    events.append(
        review_id=row.id,
        event_type="review.blocked_uncertain",
        dedupe_key="reconcile:blocked_uncertain",
        payload={"reason": "uncertain_step"},
        occurred_at=now,
        session=session,
    )
    events.append(
        review_id=row.id,
        event_type="budget.uncertain_held",
        dedupe_key="reconcile:uncertain_held",
        payload={"action": "keep_ambiguous_reservation"},
        occurred_at=now,
        session=session,
    )
    row.updated_at = now
