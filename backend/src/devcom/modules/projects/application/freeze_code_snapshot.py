from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.projects.adapters.artifact_store import ArtifactStore
from devcom.modules.projects.adapters.git_meta import capture_git_meta
from devcom.modules.projects.adapters.sqlalchemy_code_context import (
    SqlCodeContextStore,
    snapshot_from_row,
)
from devcom.modules.projects.application.code_context_support import (
    ensure_project,
    resolve_root_path,
)
from devcom.modules.projects.domain.code_artifacts import CodeSnapshot
from devcom.modules.projects.domain.errors import (
    PreviewExpiredError,
    PreviewIntegrityError,
    SnapshotNotFoundError,
)
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class FreezeCodeSnapshotCommand:
    project_id: str
    preview_id: str


class FreezeCodeSnapshot:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        store: SqlCodeContextStore,
        artifacts: ArtifactStore,
        clock: Clock,
        *,
        mode: str,
        demo_fixture: Path,
    ) -> None:
        self._sessions = sessions
        self._store = store
        self._artifacts = artifacts
        self._clock = clock
        self._mode = mode
        self._demo_fixture = demo_fixture

    def execute(self, command: FreezeCodeSnapshotCommand) -> CodeSnapshot:
        ensure_project(self._sessions, command.project_id)
        meta = self._store.get_preview_meta(command.project_id, command.preview_id)
        if meta is None:
            raise PreviewIntegrityError("preview not found for project")
        now = self._clock.now()
        if _as_utc(meta.expires_at) <= now:
            raise PreviewExpiredError("preview expired — create a new preview")
        preview_dir = self._artifacts.preview_dir(command.preview_id)
        self._artifacts.verify_fingerprint(preview_dir, meta.fingerprint)
        snapshot_id = str(uuid4())
        # Promote private preview copies — never re-read the source tree.
        target = self._artifacts.promote_preview_to_snapshot(command.preview_id, snapshot_id)
        files = self._artifacts.read_files(target)
        root, _ = resolve_root_path(
            store=self._store,
            project_id=command.project_id,
            demo_fixture=self._demo_fixture,
            mode=self._mode,
        )
        git = capture_git_meta(root)
        snapshot = CodeSnapshot(
            id=snapshot_id,
            project_id=command.project_id,
            preview_id=command.preview_id,
            fingerprint=meta.fingerprint,
            captured_at=now.isoformat(),
            files=files,
            exclusions=tuple(json.loads(meta.exclusions_json)),
            git=git,
            token_upper_bound=meta.token_upper_bound,
            token_method_blocking=meta.token_method_blocking,
            status="complete",
        )
        self._store.save_snapshot_meta(snapshot)
        return snapshot


class GetCodeSnapshot:
    def __init__(self, store: SqlCodeContextStore, artifacts: ArtifactStore) -> None:
        self._store = store
        self._artifacts = artifacts

    def execute(self, project_id: str, snapshot_id: str) -> CodeSnapshot:
        meta = self._store.get_snapshot_meta(project_id, snapshot_id)
        if meta is None or meta.status != "complete":
            raise SnapshotNotFoundError(f"snapshot {snapshot_id} not found")
        directory = self._artifacts.snapshot_dir(snapshot_id)
        files = self._artifacts.read_files(directory)
        if meta.fingerprint:
            self._artifacts.verify_fingerprint(directory, meta.fingerprint)
        return snapshot_from_row(meta, files)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
