from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_models import (
    CursorExecutionRow,
    CursorIntegrationRow,
)
from devcom.modules.missions.tech.cursor.domain.execution import CursorExecution
from devcom.modules.missions.tech.cursor.domain.execution_status import (
    ExecutionStatus,
    IntegrationStatus,
)
from devcom.modules.missions.tech.cursor.domain.integration import CursorIntegration


class SqlAlchemyExecutionStore:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def save(self, item: CursorExecution) -> None:
        with self._sessions() as session:
            row = session.get(CursorExecutionRow, item.id)
            payload = _to_row(item)
            if row is None:
                session.add(payload)
            else:
                for col in payload.__table__.columns.keys():
                    if col != "id":
                        setattr(row, col, getattr(payload, col))
            session.commit()

    def get(self, execution_id: str) -> CursorExecution | None:
        with self._sessions() as session:
            row = session.get(CursorExecutionRow, execution_id)
            return None if row is None else _from_row(row)

    def get_by_idempotency(self, key: str) -> CursorExecution | None:
        with self._sessions() as session:
            row = session.scalars(
                select(CursorExecutionRow).where(CursorExecutionRow.idempotency_key == key)
            ).first()
            return None if row is None else _from_row(row)

    def list_for_plan(self, plan_id: str) -> list[CursorExecution]:
        with self._sessions() as session:
            rows = session.scalars(
                select(CursorExecutionRow)
                .where(CursorExecutionRow.plan_id == plan_id)
                .order_by(CursorExecutionRow.created_at.desc())
            ).all()
            return [_from_row(row) for row in rows]

    def save_integration(self, item: CursorIntegration) -> None:
        with self._sessions() as session:
            row = session.get(CursorIntegrationRow, item.id)
            payload = _integration_row(item)
            if row is None:
                session.add(payload)
            else:
                for col in payload.__table__.columns.keys():
                    if col != "id":
                        setattr(row, col, getattr(payload, col))
            session.commit()

    def get_integration(self, integration_id: str) -> CursorIntegration | None:
        with self._sessions() as session:
            row = session.get(CursorIntegrationRow, integration_id)
            return None if row is None else _integration_from(row)

    def get_integration_by_idempotency(self, key: str) -> CursorIntegration | None:
        with self._sessions() as session:
            row = session.scalars(
                select(CursorIntegrationRow).where(
                    CursorIntegrationRow.idempotency_key == key
                )
            ).first()
            return None if row is None else _integration_from(row)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _to_row(item: CursorExecution) -> CursorExecutionRow:
    return CursorExecutionRow(
        id=item.id,
        project_id=item.project_id,
        plan_id=item.plan_id,
        plan_version=item.plan_version,
        content_hash=item.content_hash,
        status=item.status.value,
        correction_index=item.correction_index,
        parent_execution_id=item.parent_execution_id,
        execute_payload_hash=item.execute_payload_hash,
        execute_payload_json=item.execute_payload_json,
        approval_id=item.approval_id,
        idempotency_key=item.idempotency_key,
        source_root=item.source_root,
        git_base_commit=item.git_base_commit,
        model_id=item.model_id,
        model_fast=item.model_fast,
        sandbox_policy_version=item.sandbox_policy_version,
        reserved_eur_micros=item.reserved_eur_micros,
        worktree_path=item.worktree_path,
        agent_id=item.agent_id,
        run_id=item.run_id,
        cancel_requested=1 if item.cancel_requested else 0,
        writes_stable=1 if item.writes_stable else 0,
        capture_manifest_sha=item.capture_manifest_sha,
        capture_incomplete=1 if item.capture_incomplete else 0,
        return_id=item.return_id,
        usage_json=item.usage_json,
        billed_json=item.billed_json,
        error_message=item.error_message,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _from_row(row: CursorExecutionRow) -> CursorExecution:
    return CursorExecution(
        id=row.id,
        project_id=row.project_id,
        plan_id=row.plan_id,
        plan_version=row.plan_version,
        content_hash=row.content_hash,
        status=ExecutionStatus(row.status),
        correction_index=row.correction_index,
        parent_execution_id=row.parent_execution_id,
        execute_payload_hash=row.execute_payload_hash,
        execute_payload_json=row.execute_payload_json,
        approval_id=row.approval_id,
        idempotency_key=row.idempotency_key,
        source_root=row.source_root,
        git_base_commit=row.git_base_commit,
        model_id=row.model_id,
        model_fast=row.model_fast,
        sandbox_policy_version=row.sandbox_policy_version,
        reserved_eur_micros=row.reserved_eur_micros,
        worktree_path=row.worktree_path,
        agent_id=row.agent_id,
        run_id=row.run_id,
        cancel_requested=bool(row.cancel_requested),
        writes_stable=bool(row.writes_stable),
        capture_manifest_sha=row.capture_manifest_sha,
        capture_incomplete=bool(row.capture_incomplete),
        return_id=row.return_id,
        usage_json=row.usage_json,
        billed_json=row.billed_json,
        error_message=row.error_message,
        created_at=_aware(row.created_at),
        updated_at=_aware(row.updated_at),
    )


def _integration_row(item: CursorIntegration) -> CursorIntegrationRow:
    return CursorIntegrationRow(
        id=item.id,
        execution_id=item.execution_id,
        approval_id=item.approval_id,
        payload_hash=item.payload_hash,
        status=item.status.value,
        branch_name=item.branch_name,
        commit_sha=item.commit_sha,
        worktree_path=item.worktree_path,
        summary=item.summary,
        merge_hint=item.merge_hint,
        error_message=item.error_message,
        idempotency_key=item.idempotency_key,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _integration_from(row: CursorIntegrationRow) -> CursorIntegration:
    return CursorIntegration(
        id=row.id,
        execution_id=row.execution_id,
        approval_id=row.approval_id,
        payload_hash=row.payload_hash,
        status=IntegrationStatus(row.status),
        branch_name=row.branch_name,
        commit_sha=row.commit_sha,
        worktree_path=row.worktree_path,
        summary=row.summary,
        merge_hint=row.merge_hint,
        error_message=row.error_message,
        idempotency_key=row.idempotency_key,
        created_at=_aware(row.created_at),
        updated_at=_aware(row.updated_at),
    )
