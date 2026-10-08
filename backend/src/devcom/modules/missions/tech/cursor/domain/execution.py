from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorValidationError,
)
from devcom.modules.missions.tech.cursor.domain.execution_status import ExecutionStatus


@dataclass(slots=True)
class CursorExecution:
    id: str
    project_id: str
    plan_id: str
    plan_version: int
    content_hash: str
    status: ExecutionStatus
    correction_index: int
    parent_execution_id: str | None
    execute_payload_hash: str
    execute_payload_json: str
    approval_id: str | None
    idempotency_key: str
    source_root: str
    git_base_commit: str
    model_id: str
    model_fast: str
    sandbox_policy_version: str
    reserved_eur_micros: int
    worktree_path: str | None
    agent_id: str | None
    run_id: str | None
    cancel_requested: bool
    writes_stable: bool
    capture_manifest_sha: str | None
    capture_incomplete: bool
    return_id: str | None
    usage_json: str | None
    billed_json: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_intent(
        cls,
        *,
        project_id: str,
        plan_id: str,
        plan_version: int,
        content_hash: str,
        correction_index: int,
        parent_execution_id: str | None,
        execute_payload_hash: str,
        execute_payload_json: str,
        approval_id: str,
        idempotency_key: str,
        source_root: str,
        git_base_commit: str,
        model_id: str,
        model_fast: str,
        sandbox_policy_version: str,
        reserved_eur_micros: int,
        now: datetime,
    ) -> CursorExecution:
        if not idempotency_key.strip():
            raise CursorValidationError("idempotency key required")
        stamp = _utc(now)
        return cls(
            id=str(uuid4()),
            project_id=project_id,
            plan_id=plan_id,
            plan_version=plan_version,
            content_hash=content_hash,
            status=ExecutionStatus.INTENT,
            correction_index=correction_index,
            parent_execution_id=parent_execution_id,
            execute_payload_hash=execute_payload_hash,
            execute_payload_json=execute_payload_json,
            approval_id=approval_id,
            idempotency_key=idempotency_key.strip(),
            source_root=source_root,
            git_base_commit=git_base_commit,
            model_id=model_id,
            model_fast=model_fast,
            sandbox_policy_version=sandbox_policy_version,
            reserved_eur_micros=reserved_eur_micros,
            worktree_path=None,
            agent_id=None,
            run_id=None,
            cancel_requested=False,
            writes_stable=False,
            capture_manifest_sha=None,
            capture_incomplete=False,
            return_id=None,
            usage_json=None,
            billed_json=None,
            error_message=None,
            created_at=stamp,
            updated_at=stamp,
        )

    def mark_running(self, *, worktree: str, now: datetime) -> None:
        if self.status not in {ExecutionStatus.INTENT, ExecutionStatus.RUNNING}:
            raise CursorConflictError(f"cannot run from {self.status.value}")
        self.status = ExecutionStatus.RUNNING
        self.worktree_path = worktree
        self.updated_at = _utc(now)

    def attach_agent(self, *, agent_id: str, run_id: str, now: datetime) -> None:
        self.agent_id = agent_id
        self.run_id = run_id
        self.updated_at = _utc(now)

    def request_cancel(self, now: datetime) -> None:
        if self.status != ExecutionStatus.RUNNING:
            raise CursorConflictError("cancel only while running")
        self.cancel_requested = True
        self.status = ExecutionStatus.CANCEL_REQUESTED
        self.updated_at = _utc(now)

    def confirm_terminal(
        self,
        *,
        status: ExecutionStatus,
        writes_stable: bool,
        now: datetime,
        error_message: str | None = None,
    ) -> None:
        allowed = {
            ExecutionStatus.FINISHED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.FAILED,
            ExecutionStatus.INTERRUPTED,
            ExecutionStatus.UNCERTAIN,
        }
        if status not in allowed:
            raise CursorValidationError("invalid terminal status")
        self.status = status
        self.writes_stable = writes_stable
        self.error_message = error_message
        self.updated_at = _utc(now)

    def mark_capture(
        self,
        *,
        manifest_sha: str,
        incomplete: bool,
        now: datetime,
    ) -> None:
        self.capture_manifest_sha = manifest_sha
        self.capture_incomplete = incomplete
        if incomplete:
            self.status = ExecutionStatus.CAPTURE_INCOMPLETE
        else:
            self.status = ExecutionStatus.RETURN_READY
        self.updated_at = _utc(now)

    def attach_return(self, return_id: str, now: datetime) -> None:
        self.return_id = return_id
        self.updated_at = _utc(now)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise CursorValidationError("timestamps must be timezone-aware UTC")
    return value.astimezone(UTC)
