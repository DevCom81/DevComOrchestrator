from __future__ import annotations

from devcom.modules.projects.domain.project import Project
from devcom.modules.projects.ports.project_repository import ProjectRepository


class ListProjects:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self) -> list[Project]:
        return self._repository.list_all()
