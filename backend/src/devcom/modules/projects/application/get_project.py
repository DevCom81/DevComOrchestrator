from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.projects.domain.errors import ProjectNotFoundError
from devcom.modules.projects.domain.project import Project
from devcom.modules.projects.ports.project_repository import ProjectRepository
from devcom.shared.ids import ProjectId


@dataclass(frozen=True, slots=True)
class GetProjectQuery:
    project_id: str


class GetProject:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, query: GetProjectQuery) -> Project:
        project_id = ProjectId.parse(query.project_id)
        project = self._repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"project {project_id} not found")
        return project
