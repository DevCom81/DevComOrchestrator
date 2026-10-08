from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.approvals.adapters.sqlalchemy_store import SqlAlchemyApprovalStore
from devcom.modules.approvals.domain.approval import ApprovalRequest
from devcom.modules.approvals.domain.status import ACTION_CURSOR_EXPORT
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorNotFoundError,
    CursorValidationError,
)
from devcom.modules.missions.tech.cursor.domain.plan import CursorPlan
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class RequestCursorGoCommand:
    plan_id: str
    expected_version: int
    idempotency_key: str


class RequestCursorGo:
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

    def execute(self, command: RequestCursorGoCommand) -> tuple[CursorPlan, ApprovalRequest]:
        require_tech_action(self._policy, "cursor.plan.request_go")
        if not command.idempotency_key.strip():
            raise CursorValidationError("idempotency key required")
        existing = self._approvals.get_by_idempotency(command.idempotency_key)
        plan = self._plans.get_plan(command.plan_id)
        if plan is None:
            raise CursorNotFoundError("cursor plan not found")
        if existing is not None:
            return plan, existing
        plan.expect_version(command.expected_version)
        now = self._clock.now()
        self._approvals.invalidate_open_for_target(
            target_id=plan.id,
            action_id=ACTION_CURSOR_EXPORT,
            now=now,
        )
        approval = ApprovalRequest.create(
            action_id=ACTION_CURSOR_EXPORT,
            target_id=plan.id,
            payload_hash=plan.content_hash,
            resource_version=plan.plan_version,
            now=now,
            idempotency_key=command.idempotency_key,
        )
        self._approvals.save(approval)
        plan.mark_awaiting_go(approval.id, now)
        self._plans.save_plan(plan)
        return plan, approval
