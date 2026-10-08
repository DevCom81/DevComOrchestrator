from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.approvals.adapters.sqlalchemy_store import SqlAlchemyApprovalStore
from devcom.modules.approvals.domain.approval import ApprovalRequest
from devcom.modules.approvals.domain.status import ACTION_CURSOR_INTEGRATE
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_execution_store import (
    SqlAlchemyExecutionStore,
)
from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorNotFoundError,
    CursorValidationError,
)
from devcom.modules.missions.tech.cursor.domain.execute_canon import integrate_payload_hash
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class RequestIntegrateGoCommand:
    execution_id: str
    idempotency_key: str


class RequestIntegrateGo:
    def __init__(
        self,
        *,
        executions: SqlAlchemyExecutionStore,
        approvals: SqlAlchemyApprovalStore,
        policy: PermissionPolicy,
        clock: Clock,
    ) -> None:
        self._executions = executions
        self._approvals = approvals
        self._policy = policy
        self._clock = clock

    def execute(
        self, command: RequestIntegrateGoCommand
    ) -> tuple[dict[str, object], ApprovalRequest]:
        require_tech_action(self._policy, "cursor.integrate.request_go")
        if not command.idempotency_key.strip():
            raise CursorValidationError("idempotency key required")
        execution = self._executions.get(command.execution_id)
        if execution is None:
            raise CursorNotFoundError("execution not found")
        if not execution.capture_manifest_sha or execution.capture_incomplete:
            raise CursorConflictError("no stable capture to integrate")
        existing = self._approvals.get_by_idempotency(command.idempotency_key)
        branch = f"devcom/cursor/{execution.id}"
        digest = integrate_payload_hash(
            execution_id=execution.id,
            capture_manifest_sha=execution.capture_manifest_sha,
            source_root=execution.source_root,
            git_base_commit=execution.git_base_commit,
            branch_name=branch,
        )
        preview: dict[str, object] = {
            "execution_id": execution.id,
            "capture_manifest_sha": execution.capture_manifest_sha,
            "source_root": execution.source_root,
            "git_base_commit": execution.git_base_commit,
            "branch_name": branch,
            "payload_hash": digest,
            "effects": (
                "Creates local branch via isolated worktree and one local commit. "
                "Does not modify daily working tree, merge, or push."
            ),
        }
        if existing is not None:
            return preview, existing
        now = self._clock.now()
        self._approvals.invalidate_open_for_target(
            target_id=execution.id,
            action_id=ACTION_CURSOR_INTEGRATE,
            now=now,
        )
        approval = ApprovalRequest.create(
            action_id=ACTION_CURSOR_INTEGRATE,
            target_id=execution.id,
            payload_hash=digest,
            resource_version=1,
            now=now,
            idempotency_key=command.idempotency_key,
        )
        self._approvals.save(approval)
        return preview, approval
