from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.billing.adapters.sqlalchemy_ledger import SqlAlchemyBudgetLedger
from devcom.modules.missions.tech.adapters.sqlalchemy_models import TechReviewRow
from devcom.modules.missions.tech.adapters.sqlalchemy_steps import SqlAlchemyStepStore
from devcom.modules.missions.tech.domain.status import ExecutionMode, TechReviewStatus
from devcom.shared.time import Clock


def reconcile_interrupted_real_pipeline(
    *,
    session_factory: sessionmaker[Session],
    steps: SqlAlchemyStepStore,
    ledger: SqlAlchemyBudgetLedger,
    clock: Clock,
) -> int:
    """Mark in-flight steps uncertain; never auto-resume paid calls."""
    marked = steps.mark_in_flight_uncertain()
    ledger.clear_stale_lock()
    if marked == 0:
        return 0
    now = clock.now()
    with session_factory() as session:
        rows = session.scalars(
            select(TechReviewRow).where(
                TechReviewRow.execution_mode == ExecutionMode.REAL.value,
                TechReviewRow.status == TechReviewStatus.RUNNING.value,
            )
        ).all()
        for row in rows:
            row.status = TechReviewStatus.BLOCKED_UNCERTAIN.value
            row.failure_message = (
                "interrupted while a call was in flight — "
                "no automatic replay; cost may be uncertain"
            )
            row.updated_at = now
        session.commit()
    return marked
