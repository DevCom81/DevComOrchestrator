from __future__ import annotations

from datetime import datetime

from devcom.modules.billing.adapters.sqlalchemy_ledger import SqlAlchemyBudgetLedger
from devcom.modules.missions.tech.adapters.sqlalchemy_events import SqlAlchemyEventStore
from devcom.modules.missions.tech.adapters.sqlalchemy_steps import SqlAlchemyStepStore
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import TechReviewStatus
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository


def settle_if_safe(
    *,
    steps: SqlAlchemyStepStore,
    ledger: SqlAlchemyBudgetLedger,
    events: SqlAlchemyEventStore,
    review_id: str,
    now: datetime,
) -> None:
    ambiguous = any(
        item["status"] == "uncertain" or item.get("cost_status") == "uncertain"
        for item in steps.list_steps(review_id)
    )
    if ambiguous:
        events.append(
            review_id=review_id,
            event_type="budget.uncertain_held",
            dedupe_key="budget.uncertain_held:executor",
            payload={"action": "keep_ambiguous_reservation"},
            occurred_at=now,
        )
        return
    ledger.release_unused_envelope(review_id)
    events.append(
        review_id=review_id,
        event_type="budget.settled",
        dedupe_key="budget.settled:executor",
        payload={"reason": "non_ambiguous"},
        occurred_at=now,
    )


def fail_review(
    *,
    repository: TechReviewRepository,
    steps: SqlAlchemyStepStore,
    ledger: SqlAlchemyBudgetLedger,
    events: SqlAlchemyEventStore,
    review: TechReview,
    message: str,
    status: TechReviewStatus,
    now: datetime,
) -> None:
    settle_if_safe(steps=steps, ledger=ledger, events=events, review_id=review.id, now=now)
    review.status = status
    review.failure_message = message
    review.updated_at = now
    repository.save_atomic(review)
    event_type = (
        "review.blocked_uncertain"
        if status == TechReviewStatus.BLOCKED_UNCERTAIN
        else "review.terminal"
    )
    events.append(
        review_id=review.id,
        event_type=event_type,
        dedupe_key=f"{event_type}:{status.value}",
        payload={"status": status.value, "message": message[:200]},
        occurred_at=now,
    )
