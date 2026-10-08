from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.approvals.adapters.sqlalchemy_models import ApprovalRequestRow
from devcom.modules.approvals.domain.approval import ApprovalRequest
from devcom.modules.approvals.domain.errors import ApprovalNotFoundError
from devcom.modules.approvals.domain.status import ApprovalStatus
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_models import (
    CursorExportRow,
    CursorPlanRow,
)
from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorNotFoundError,
    CursorValidationError,
)
from devcom.modules.missions.tech.cursor.domain.status import CursorPlanStatus
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class ExportCursorPlanCommand:
    plan_id: str
    idempotency_key: str


class ExportCursorPlan:
    def __init__(
        self,
        *,
        sessions: sessionmaker[Session],
        plans: SqlAlchemyCursorStore,
        policy: PermissionPolicy,
        clock: Clock,
    ) -> None:
        self._sessions = sessions
        self._plans = plans
        self._policy = policy
        self._clock = clock

    def execute(self, command: ExportCursorPlanCommand) -> dict[str, Any]:
        require_tech_action(self._policy, "cursor.plan.export")
        if not command.idempotency_key.strip():
            raise CursorValidationError("idempotency key required")
        existing = self._plans.get_export_by_idempotency(command.idempotency_key)
        if existing is not None:
            return existing
        plan = self._plans.get_plan(command.plan_id)
        if plan is None:
            raise CursorNotFoundError("cursor plan not found")
        if plan.active_approval_id is None:
            raise CursorConflictError("no active GO for this plan")
        now = self._clock.now()
        with self._sessions() as session:
            approval_row = session.get(ApprovalRequestRow, plan.active_approval_id)
            if approval_row is None:
                raise ApprovalNotFoundError("approval not found")
            approval = _approval_from_row(approval_row)
            approval.consume_for_export(
                payload_hash=plan.content_hash,
                resource_version=plan.plan_version,
                now=now,
            )
            approval_row.status = approval.status.value
            approval_row.consumed_at = approval.consumed_at
            export_id = str(uuid4())
            manifest_json = json.dumps(
                plan.approved_manifest(), ensure_ascii=False, sort_keys=True
            )
            session.add(
                CursorExportRow(
                    id=export_id,
                    plan_id=plan.id,
                    plan_version=plan.plan_version,
                    content_hash=plan.content_hash,
                    approval_id=approval.id,
                    markdown_utf8=plan.markdown_utf8,
                    manifest_json=manifest_json,
                    idempotency_key=command.idempotency_key,
                    created_at=now,
                )
            )
            plan_row = session.get(CursorPlanRow, plan.id)
            if plan_row is None:
                raise CursorNotFoundError("cursor plan not found")
            plan_row.status = CursorPlanStatus.EXPORTED.value
            plan_row.updated_at = now
            session.commit()
        loaded = self._plans.get_export(export_id)
        assert loaded is not None
        return loaded


def _approval_from_row(row: ApprovalRequestRow) -> ApprovalRequest:
    return ApprovalRequest(
        id=row.id,
        action_id=row.action_id,
        target_id=row.target_id,
        payload_hash=row.payload_hash,
        resource_version=row.resource_version,
        status=ApprovalStatus(row.status),
        author=row.author,
        created_at=_aware(row.created_at),
        expires_at=_aware(row.expires_at),
        decided_at=_aware_opt(row.decided_at),
        consumed_at=_aware_opt(row.consumed_at),
        idempotency_key=row.idempotency_key,
    )


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _aware_opt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _aware(value)
