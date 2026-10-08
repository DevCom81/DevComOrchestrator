from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.approvals.adapters.sqlalchemy_store import SqlAlchemyApprovalStore
from devcom.modules.approvals.domain.approval import ApprovalRequest
from devcom.modules.approvals.domain.errors import ApprovalNotFoundError
from devcom.modules.approvals.domain.status import (
    ACTION_CURSOR_EXECUTE,
    ACTION_CURSOR_EXPORT,
    ACTION_CURSOR_INTEGRATE,
)
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.domain.errors import CursorConflictError
from devcom.shared.time import Clock

_ALLOWED = {ACTION_CURSOR_EXPORT, ACTION_CURSOR_EXECUTE, ACTION_CURSOR_INTEGRATE}


@dataclass(frozen=True, slots=True)
class DecideCursorGoCommand:
    approval_id: str
    grant: bool


class DecideCursorGo:
    """Human governance grant/refuse — not an EXTERNAL recursive approval."""

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

    def execute(self, command: DecideCursorGoCommand) -> ApprovalRequest:
        require_tech_action(self._policy, "cursor.plan.decide_go")
        approval = self._approvals.get(command.approval_id)
        if approval is None:
            raise ApprovalNotFoundError("approval not found")
        if approval.action_id not in _ALLOWED:
            raise CursorConflictError("approval is not a cursor GO")
        now = self._clock.now()
        if command.grant:
            approval.grant(now)
        else:
            approval.refuse(now)
        self._approvals.save(approval)
        if approval.action_id != ACTION_CURSOR_EXPORT:
            return approval
        plan = self._plans.get_plan(approval.target_id)
        if plan is not None and plan.active_approval_id == approval.id:
            if command.grant:
                plan.mark_go_granted(now)
            else:
                plan.active_approval_id = None
                from devcom.modules.missions.tech.cursor.domain.status import CursorPlanStatus

                plan.status = CursorPlanStatus.DRAFT
                plan.updated_at = now
            self._plans.save_plan(plan)
        return approval
