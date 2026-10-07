from __future__ import annotations

from typing import Protocol

from devcom.modules.projects.domain.project import Project
from devcom.shared.ids import ProjectId


class ProjectRepository(Protocol):
    def save(self, project: Project) -> None:
        """Insert or update a project."""

    def get_by_id(self, project_id: ProjectId) -> Project | None:
        """Return a project or None when missing."""

    def list_all(self) -> list[Project]:
        """Return projects ordered by updated_at descending."""
