from __future__ import annotations

from devcom.modules.projects.adapters.artifact_store import ArtifactStore
from devcom.modules.projects.adapters.sqlalchemy_code_context import SqlCodeContextStore
from devcom.modules.projects.application.freeze_code_snapshot import GetCodeSnapshot
from devcom.modules.projects.domain.code_artifacts import CodeSnapshot


class ProjectCodeSnapshotAdapter:
    def __init__(self, store: SqlCodeContextStore, artifacts: ArtifactStore) -> None:
        self._get = GetCodeSnapshot(store, artifacts)

    def get(self, project_id: str, snapshot_id: str) -> CodeSnapshot:
        return self._get.execute(project_id, snapshot_id)
