from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.application.defaults import default_sections
from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorNotFoundError,
    CursorValidationError,
)
from devcom.modules.missions.tech.cursor.domain.plan import CursorPlan
from devcom.modules.missions.tech.domain.status import TechReviewStatus
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class CreateCursorPlanCommand:
    review_id: str


class CreateCursorPlan:
    def __init__(
        self,
        *,
        reviews: TechReviewRepository,
        plans: SqlAlchemyCursorStore,
        policy: PermissionPolicy,
        clock: Clock,
    ) -> None:
        self._reviews = reviews
        self._plans = plans
        self._policy = policy
        self._clock = clock

    def execute(self, command: CreateCursorPlanCommand) -> CursorPlan:
        require_tech_action(self._policy, "cursor.plan.edit")
        review = self._reviews.get_by_id(command.review_id)
        if review is None:
            raise CursorNotFoundError("tech review not found")
        if review.status != TechReviewStatus.DECIDED:
            raise CursorConflictError("cursor plan requires a decided tech review")
        if review.decision is None or review.adr is None:
            raise CursorValidationError("decision and ADR required")
        existing = self._plans.list_plans_for_review(review.id)
        if existing:
            return existing[0]
        plan = CursorPlan.create(
            project_id=review.project_id,
            review_id=review.id,
            proposal_id=review.decision.proposal_id,
            proposal_version=review.decision.proposal_version,
            adr_id=review.adr.id,
            code_snapshot_id=review.code_snapshot_id,
            sections=default_sections(review),
            now=self._clock.now(),
        )
        self._plans.save_plan(plan)
        return plan
