from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.projects.adapters.code_context_models import (
    CodePreviewRow,
    CodeSnapshotRow,
    ProjectSourceRootRow,
)
from devcom.modules.projects.domain.code_artifacts import (
    CodePreview,
    CodeSnapshot,
    FileBlob,
    GitCaptureMeta,
)
from devcom.modules.projects.domain.errors import ProjectNotFoundError


class SqlCodeContextStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sessions = session_factory

    def get_root(self, project_id: str) -> tuple[str, tuple[str, ...], datetime] | None:
        with self._sessions() as session:
            row = session.get(ProjectSourceRootRow, project_id)
            if row is None:
                return None
            globs = tuple(json.loads(row.exclusions_json))
            return row.absolute_path, globs, row.attached_at

    def upsert_root(
        self,
        *,
        project_id: str,
        absolute_path: str,
        exclusions: tuple[str, ...],
        attached_at: datetime,
    ) -> None:
        with self._sessions() as session:
            row = session.get(ProjectSourceRootRow, project_id)
            if row is None:
                session.add(
                    ProjectSourceRootRow(
                        project_id=project_id,
                        absolute_path=absolute_path,
                        exclusions_json=json.dumps(list(exclusions)),
                        attached_at=attached_at,
                    )
                )
            else:
                row.absolute_path = absolute_path
                row.exclusions_json = json.dumps(list(exclusions))
                row.attached_at = attached_at
            session.commit()

    def delete_root(self, project_id: str) -> None:
        with self._sessions() as session:
            row = session.get(ProjectSourceRootRow, project_id)
            if row is not None:
                session.delete(row)
                session.commit()

    def save_preview_meta(self, preview: CodePreview) -> None:
        with self._sessions() as session:
            session.add(
                CodePreviewRow(
                    id=preview.id,
                    project_id=preview.project_id,
                    fingerprint=preview.fingerprint,
                    created_at=_parse(preview.created_at),
                    expires_at=_parse(preview.expires_at),
                    exclusions_json=json.dumps(list(preview.exclusions)),
                    token_upper_bound=preview.token_upper_bound,
                    token_indicative=preview.token_indicative,
                    token_method_blocking=preview.token_method_blocking,
                    token_method_indicative=preview.token_method_indicative,
                    status="ready",
                )
            )
            session.commit()

    def get_preview_meta(self, project_id: str, preview_id: str) -> CodePreviewRow | None:
        with self._sessions() as session:
            row = session.get(CodePreviewRow, preview_id)
            if row is None or row.project_id != project_id:
                return None
            session.expunge(row)
            return row

    def save_snapshot_meta(self, snapshot: CodeSnapshot) -> None:
        with self._sessions() as session:
            dirty = None if snapshot.git.dirty is None else int(snapshot.git.dirty)
            session.add(
                CodeSnapshotRow(
                    id=snapshot.id,
                    project_id=snapshot.project_id,
                    preview_id=snapshot.preview_id,
                    fingerprint=snapshot.fingerprint,
                    captured_at=_parse(snapshot.captured_at),
                    exclusions_json=json.dumps(list(snapshot.exclusions)),
                    git_commit=snapshot.git.commit,
                    git_dirty=dirty,
                    git_note=snapshot.git.note,
                    token_upper_bound=snapshot.token_upper_bound,
                    token_method_blocking=snapshot.token_method_blocking,
                    status=snapshot.status,
                )
            )
            session.commit()

    def get_snapshot_meta(self, project_id: str, snapshot_id: str) -> CodeSnapshotRow | None:
        with self._sessions() as session:
            row = session.get(CodeSnapshotRow, snapshot_id)
            if row is None or row.project_id != project_id:
                return None
            session.expunge(row)
            return row

    def list_snapshot_metas(self, project_id: str) -> list[CodeSnapshotRow]:
        with self._sessions() as session:
            rows = session.scalars(
                select(CodeSnapshotRow)
                .where(CodeSnapshotRow.project_id == project_id)
                .order_by(CodeSnapshotRow.captured_at.desc())
            ).all()
            for row in rows:
                session.expunge(row)
            return list(rows)


def require_project_exists(session: Session, project_id: str) -> None:
    from devcom.modules.projects.adapters.sqlalchemy_models import ProjectRow

    if session.get(ProjectRow, project_id) is None:
        raise ProjectNotFoundError(f"project {project_id} not found")


def snapshot_from_row(row: CodeSnapshotRow, files: tuple[FileBlob, ...]) -> CodeSnapshot:
    dirty = None if row.git_dirty is None else bool(row.git_dirty)
    return CodeSnapshot(
        id=row.id,
        project_id=row.project_id,
        preview_id=row.preview_id,
        fingerprint=row.fingerprint,
        captured_at=row.captured_at.isoformat(),
        files=files,
        exclusions=tuple(json.loads(row.exclusions_json)),
        git=GitCaptureMeta(commit=row.git_commit, dirty=dirty, note=row.git_note),
        token_upper_bound=row.token_upper_bound,
        token_method_blocking=row.token_method_blocking,
        status=row.status,
    )


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value)
