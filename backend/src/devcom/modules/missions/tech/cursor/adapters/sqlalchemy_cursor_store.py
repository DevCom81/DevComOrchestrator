from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_models import (
    CursorExportRow,
    CursorPlanRow,
    CursorReturnRow,
)
from devcom.modules.missions.tech.cursor.domain.plan import CursorPlan
from devcom.modules.missions.tech.cursor.domain.status import CursorPlanStatus


class SqlAlchemyCursorStore:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def save_plan(self, plan: CursorPlan) -> None:
        with self._sessions() as session:
            row = session.get(CursorPlanRow, plan.id)
            payload = _plan_row(plan)
            if row is None:
                session.add(payload)
            else:
                for col in payload.__table__.columns.keys():
                    if col != "id":
                        setattr(row, col, getattr(payload, col))
            session.commit()

    def get_plan(self, plan_id: str) -> CursorPlan | None:
        with self._sessions() as session:
            row = session.get(CursorPlanRow, plan_id)
            return None if row is None else _plan_from(row)

    def list_plans_for_review(self, review_id: str) -> list[CursorPlan]:
        with self._sessions() as session:
            rows = session.scalars(
                select(CursorPlanRow)
                .where(CursorPlanRow.review_id == review_id)
                .order_by(CursorPlanRow.created_at.desc())
            ).all()
            return [_plan_from(row) for row in rows]

    def save_export(self, data: dict[str, Any]) -> None:
        with self._sessions() as session:
            session.add(
                CursorExportRow(
                    id=data["id"],
                    plan_id=data["plan_id"],
                    plan_version=data["plan_version"],
                    content_hash=data["content_hash"],
                    approval_id=data["approval_id"],
                    markdown_utf8=data["markdown_utf8"],
                    manifest_json=data["manifest_json"],
                    idempotency_key=data["idempotency_key"],
                    created_at=data["created_at"],
                )
            )
            session.commit()

    def get_export(self, export_id: str) -> dict[str, Any] | None:
        with self._sessions() as session:
            row = session.get(CursorExportRow, export_id)
            return None if row is None else _export_dict(row)

    def get_export_by_idempotency(self, key: str) -> dict[str, Any] | None:
        with self._sessions() as session:
            row = session.scalars(
                select(CursorExportRow).where(CursorExportRow.idempotency_key == key)
            ).first()
            return None if row is None else _export_dict(row)

    def list_exports(self, plan_id: str) -> list[dict[str, Any]]:
        with self._sessions() as session:
            rows = session.scalars(
                select(CursorExportRow)
                .where(CursorExportRow.plan_id == plan_id)
                .order_by(CursorExportRow.created_at.desc())
            ).all()
            return [_export_dict(row) for row in rows]

    def save_return(self, data: dict[str, Any]) -> None:
        with self._sessions() as session:
            session.add(CursorReturnRow(**data))
            session.commit()

    def get_return(self, return_id: str) -> dict[str, Any] | None:
        with self._sessions() as session:
            row = session.get(CursorReturnRow, return_id)
            return None if row is None else _return_dict(row)

    def list_returns(self, plan_id: str) -> list[dict[str, Any]]:
        with self._sessions() as session:
            rows = session.scalars(
                select(CursorReturnRow)
                .where(CursorReturnRow.plan_id == plan_id)
                .order_by(CursorReturnRow.imported_at.desc())
            ).all()
            return [_return_dict(row) for row in rows]

    def set_return_linked_review(self, return_id: str, review_id: str) -> None:
        with self._sessions() as session:
            row = session.get(CursorReturnRow, return_id)
            if row is not None:
                row.linked_review_id = review_id
                session.commit()


def _plan_row(plan: CursorPlan) -> CursorPlanRow:
    return CursorPlanRow(
        id=plan.id,
        project_id=plan.project_id,
        review_id=plan.review_id,
        proposal_id=plan.proposal_id,
        proposal_version=plan.proposal_version,
        adr_id=plan.adr_id,
        code_snapshot_id=plan.code_snapshot_id,
        status=plan.status.value,
        plan_version=plan.plan_version,
        objectif=plan.objectif,
        perimetre=plan.perimetre,
        exclusions=plan.exclusions,
        contraintes_architecture=plan.contraintes_architecture,
        criteres_acceptation=plan.criteres_acceptation,
        validations_attendues=plan.validations_attendues,
        markdown_utf8=plan.markdown_utf8,
        metadata_json=plan.metadata_json,
        content_hash=plan.content_hash,
        canon_version=plan.canon_version,
        active_approval_id=plan.active_approval_id,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def _plan_from(row: CursorPlanRow) -> CursorPlan:
    return CursorPlan(
        id=row.id,
        project_id=row.project_id,
        review_id=row.review_id,
        proposal_id=row.proposal_id,
        proposal_version=row.proposal_version,
        adr_id=row.adr_id,
        code_snapshot_id=row.code_snapshot_id,
        status=CursorPlanStatus(row.status),
        plan_version=row.plan_version,
        objectif=row.objectif,
        perimetre=row.perimetre,
        exclusions=row.exclusions,
        contraintes_architecture=row.contraintes_architecture,
        criteres_acceptation=row.criteres_acceptation,
        validations_attendues=row.validations_attendues,
        markdown_utf8=row.markdown_utf8,
        metadata_json=row.metadata_json,
        content_hash=row.content_hash,
        canon_version=row.canon_version,
        active_approval_id=row.active_approval_id,
        created_at=_aware(row.created_at),
        updated_at=_aware(row.updated_at),
    )


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _export_dict(row: CursorExportRow) -> dict[str, Any]:
    created = row.created_at if row.created_at.tzinfo else row.created_at.replace(tzinfo=UTC)
    return {
        "id": row.id,
        "plan_id": row.plan_id,
        "plan_version": row.plan_version,
        "content_hash": row.content_hash,
        "approval_id": row.approval_id,
        "markdown_utf8": row.markdown_utf8,
        "manifest_json": row.manifest_json,
        "manifest": json.loads(row.manifest_json),
        "idempotency_key": row.idempotency_key,
        "created_at": created,
    }


def _return_dict(row: CursorReturnRow) -> dict[str, Any]:
    imported = row.imported_at if row.imported_at.tzinfo else row.imported_at.replace(tzinfo=UTC)
    return {
        "id": row.id,
        "plan_id": row.plan_id,
        "export_id": row.export_id,
        "project_id": row.project_id,
        "report_sha256": row.report_sha256,
        "diff_sha256": row.diff_sha256,
        "report_bytes": row.report_bytes,
        "diff_bytes": row.diff_bytes,
        "declared_base": row.declared_base,
        "declared_commit": row.declared_commit,
        "verification_status": row.verification_status,
        "verification_notes": row.verification_notes,
        "artifact_dir": row.artifact_dir,
        "linked_review_id": row.linked_review_id,
        "imported_at": imported,
    }
