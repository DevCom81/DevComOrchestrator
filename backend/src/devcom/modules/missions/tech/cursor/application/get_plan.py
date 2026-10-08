from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.domain.errors import CursorNotFoundError
from devcom.modules.missions.tech.cursor.domain.plan import CursorPlan


@dataclass(frozen=True, slots=True)
class GetCursorPlanQuery:
    plan_id: str


class GetCursorPlan:
    def __init__(self, plans: SqlAlchemyCursorStore) -> None:
        self._plans = plans

    def execute(self, query: GetCursorPlanQuery) -> CursorPlan:
        plan = self._plans.get_plan(query.plan_id)
        if plan is None:
            raise CursorNotFoundError("cursor plan not found")
        return plan


@dataclass(frozen=True, slots=True)
class ListCursorPlansQuery:
    review_id: str


class ListCursorPlans:
    def __init__(self, plans: SqlAlchemyCursorStore) -> None:
        self._plans = plans

    def execute(self, query: ListCursorPlansQuery) -> list[CursorPlan]:
        return self._plans.list_plans_for_review(query.review_id)
