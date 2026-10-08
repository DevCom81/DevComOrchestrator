from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from devcom.modules.missions.tech.cursor.domain.errors import CursorValidationError
from devcom.modules.missions.tech.cursor.domain.execution_status import IntegrationStatus


@dataclass(slots=True)
class CursorIntegration:
    id: str
    execution_id: str
    approval_id: str
    payload_hash: str
    status: IntegrationStatus
    branch_name: str
    commit_sha: str | None
    worktree_path: str | None
    summary: str | None
    merge_hint: str | None
    error_message: str | None
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        execution_id: str,
        approval_id: str,
        payload_hash: str,
        branch_name: str,
        idempotency_key: str,
        now: datetime,
    ) -> CursorIntegration:
        stamp = _utc(now)
        return cls(
            id=str(uuid4()),
            execution_id=execution_id,
            approval_id=approval_id,
            payload_hash=payload_hash,
            status=IntegrationStatus.PROPOSED,
            branch_name=branch_name,
            commit_sha=None,
            worktree_path=None,
            summary=None,
            merge_hint=None,
            error_message=None,
            idempotency_key=idempotency_key,
            created_at=stamp,
            updated_at=stamp,
        )

    def mark_applied(
        self,
        *,
        commit_sha: str,
        worktree_path: str,
        summary: str,
        merge_hint: str,
        now: datetime,
    ) -> None:
        self.status = IntegrationStatus.APPLIED
        self.commit_sha = commit_sha
        self.worktree_path = worktree_path
        self.summary = summary
        self.merge_hint = merge_hint
        self.updated_at = _utc(now)

    def mark_failed(self, message: str, now: datetime) -> None:
        self.status = IntegrationStatus.FAILED
        self.error_message = message
        self.updated_at = _utc(now)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise CursorValidationError("timestamps must be timezone-aware UTC")
    return value.astimezone(UTC)
