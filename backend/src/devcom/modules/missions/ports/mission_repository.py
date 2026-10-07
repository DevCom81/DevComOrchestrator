from __future__ import annotations

from typing import Protocol

from devcom.modules.missions.domain.mission import Mission


class MissionRepository(Protocol):
    def save_atomic(self, mission: Mission) -> None:
        """Persist mission, tasks and authorization block atomically."""

    def get_by_id(self, mission_id: str) -> Mission | None:
        """Return mission or None."""

    def list_for_project(self, project_id: str | None) -> list[Mission]:
        """List missions, optionally filtered by project."""
