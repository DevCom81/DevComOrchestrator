from __future__ import annotations

from typing import Protocol

from devcom.modules.missions.tech.domain.artifacts import ContextSnapshot


class ProjectSnapshotPort(Protocol):
    def capture(self, project_id: str, captured_at: str) -> ContextSnapshot:
        """Freeze current project fields into a snapshot."""
