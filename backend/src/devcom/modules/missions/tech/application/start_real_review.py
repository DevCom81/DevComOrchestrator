from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from devcom.modules.billing.adapters.rate_tables import FxTable, OpenAiRateTable
from devcom.modules.billing.adapters.sqlalchemy_ledger import SqlAlchemyBudgetLedger
from devcom.modules.billing.domain.errors import (
    PipelineLockError,
    RealModeUnavailableError,
)
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.adapters.sqlalchemy_events import SqlAlchemyEventStore
from devcom.modules.missions.tech.adapters.sqlalchemy_steps import SqlAlchemyStepStore
from devcom.modules.missions.tech.application.idempotency import (
    payload_hash,
    resolve_idempotency,
)
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.application.supervised_runner import SupervisedRealRunner
from devcom.modules.missions.tech.domain.errors import (
    TechNotFoundError,
    TechValidationError,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import (
    IDEM_RUN,
    ExecutionMode,
    TechReviewStatus,
)
from devcom.modules.missions.tech.ports.idempotency_store import IdempotencyStore
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class StartRealTechReviewCommand:
    review_id: str
    idempotency_key: str


class StartRealTechReview:
    def __init__(
        self,
        *,
        repository: TechReviewRepository,
        steps: SqlAlchemyStepStore,
        ledger: SqlAlchemyBudgetLedger,
        events: SqlAlchemyEventStore,
        runner: SupervisedRealRunner,
        policy: PermissionPolicy,
        idempotency: IdempotencyStore,
        rates: OpenAiRateTable,
        fx: FxTable,
        real_mode_enabled: bool,
        openai_configured: bool,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._steps = steps
        self._ledger = ledger
        self._events = events
        self._runner = runner
        self._policy = policy
        self._idempotency = idempotency
        self._rates = rates
        self._fx = fx
        self._real_enabled = real_mode_enabled
        self._openai_configured = openai_configured
        self._clock = clock

    def execute(self, command: StartRealTechReviewCommand) -> TechReview:
        require_tech_action(self._policy, "tech.review.run")
        if not command.idempotency_key.strip():
            raise TechValidationError("idempotency key is required")
        if not self._real_enabled:
            raise RealModeUnavailableError("real mode is disabled")
        if not self._openai_configured:
            raise RealModeUnavailableError("OPENAI_API_KEY absent — refusing real launch")
        digest = payload_hash({"review_id": command.review_id, "mode": "real"})
        existing_id = resolve_idempotency(
            self._idempotency,
            operation=IDEM_RUN,
            key=command.idempotency_key,
            expected_hash=digest,
        )
        if existing_id is not None:
            return self._require(existing_id)
        return self._start(command, digest)

    def _start(self, command: StartRealTechReviewCommand, digest: str) -> TechReview:
        review = self._require(command.review_id)
        if review.execution_mode != ExecutionMode.REAL:
            raise TechValidationError("review is not in real execution mode")
        if review.status in {
            TechReviewStatus.RUNNING,
            TechReviewStatus.AWAITING_DECISION,
            TechReviewStatus.DECIDED,
            TechReviewStatus.FAILED_PARTIAL,
            TechReviewStatus.BLOCKED_UNCERTAIN,
            TechReviewStatus.INTERRUPTED,
            TechReviewStatus.PAUSED_BUDGET,
        }:
            return review
        if review.status != TechReviewStatus.READY_TO_RUN:
            raise TechValidationError("review is not ready to run")
        if review.plan_json is None or review.envelope_eur_micros is None:
            raise TechValidationError("real plan/envelope missing")
        if review.snapshot is None:
            raise TechValidationError("snapshot missing")
        now = self._clock.now()
        if not self._ledger.try_acquire_global_lock(review.id, now):
            raise PipelineLockError("another real review is already active")
        try:
            self._persist_launch(review, command, digest, now)
        except Exception:
            self._ledger.release_global_lock(review.id)
            raise
        self._runner.start(review.id)
        return self._require(review.id)

    def _persist_launch(
        self,
        review: TechReview,
        command: StartRealTechReviewCommand,
        digest: str,
        now: datetime,
    ) -> None:
        self._ledger.reserve_review_envelope(
            review_id=review.id,
            envelope_usd_micros=review.envelope_usd_micros or 0,
            envelope_eur_micros=review.envelope_eur_micros or 0,
            fx_rate=self._fx.rate,
            fx_rate_date=self._fx.rate_date,
            fx_margin_ratio=self._fx.fx_margin_ratio,
            rates_verified_at=self._rates.verified_at,
            now=now,
        )
        if not self._steps.list_steps(review.id):
            self._steps.replace_plan(review.id, json.loads(review.plan_json or "[]"))
        review.mark_running(now)
        self._repository.save_atomic(
            review,
            idem_operation=IDEM_RUN,
            idem_key=command.idempotency_key,
            idem_hash=digest,
        )
        self._events.append(
            review_id=review.id,
            event_type="budget.reserved",
            dedupe_key="budget.reserved:launch",
            payload={"envelope_eur_micros": review.envelope_eur_micros or 0},
            occurred_at=now,
        )
        self._events.append(
            review_id=review.id,
            event_type="review.started",
            dedupe_key="review.started:launch",
            payload={"execution_mode": "real"},
            occurred_at=now,
        )

    def _require(self, review_id: str) -> TechReview:
        review = self._repository.get_by_id(review_id)
        if review is None:
            raise TechNotFoundError(f"tech review {review_id} not found")
        return review
