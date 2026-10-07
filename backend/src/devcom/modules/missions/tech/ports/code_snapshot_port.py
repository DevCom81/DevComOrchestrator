from __future__ import annotations

from typing import Protocol

from devcom.modules.projects.domain.code_artifacts import CodeSnapshot


class CodeSnapshotPort(Protocol):
    def get(self, project_id: str, snapshot_id: str) -> CodeSnapshot: ...
