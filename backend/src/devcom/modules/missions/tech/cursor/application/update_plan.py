from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.approvals.adapters.sqlalchemy_store import SqlAlchemyApprovalStore
from devcom.modules.approvals.domain.status import ACTION_CURSOR_EXPORT
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.domain.errors import CursorNotFoundError
from devcom.modules.missions.tech.cursor.domain.plan import CursorPlan
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class UpdateCursorPlanCommand:
    plan_id: str
    expected_version: int
    objectif: str
    perimetre: str
    exclusions: str
    contraintes_architecture: str
    criteres_acceptation: str
    validations_attendues: str


class UpdateCursorPlan:
    def __init__(
        self,
        *,
        plans: SqlAlchemyCursorStore,
        approvals: SqlAlchemyApprovalStore,
        policy: PermissionPolicy,
        clock: Clock,
    ) -> None:
        self._plans = plans
        self._approvals = approvals
        self._policy = policy
        self._clock = clock

    def execute(self, command: UpdateCursorPlanCommand) -> CursorPlan:
        require_tech_action(self._policy, "cursor.plan.edit")
        plan = self._plans.get_plan(command.plan_id)
        if plan is None:
            raise CursorNotFoundError("cursor plan not found")
        plan.expect_version(command.expected_version)
        now = self._clock.now()
        self._approvals.invalidate_open_for_target(
            target_id=plan.id,
            action_id=ACTION_CURSOR_EXPORT,
            now=now,
        )
        plan.update_sections(
            {
                "objectif": command.objectif,
                "perimetre": command.perimetre,
                "exclusions": command.exclusions,
                "contraintes_architecture": command.contraintes_architecture,
                "criteres_acceptation": command.criteres_acceptation,
                "validations_attendues": command.validations_attendues,
            },
            now=now,
        )
        self._plans.save_plan(plan)
        return plan
