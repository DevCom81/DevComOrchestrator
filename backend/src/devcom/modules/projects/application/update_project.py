from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.projects.domain.errors import (
    ProjectNotFoundError,
    ProjectValidationError,
)
from devcom.modules.projects.domain.project import (
    Project,
    ProjectDescription,
    ProjectName,
)
from devcom.modules.projects.ports.project_repository import ProjectRepository
from devcom.shared.ids import ProjectId
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class UpdateProjectCommand:
    project_id: str
    name: str | None
    description: str | None


class UpdateProject:
    def __init__(self, repository: ProjectRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, command: UpdateProjectCommand) -> Project:
        if command.name is None and command.description is None:
            raise ProjectValidationError("at least one of name or description is required")
        project_id = ProjectId.parse(command.project_id)
        project = self._repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"project {project_id} not found")
        project.update(
            name=None if command.name is None else ProjectName.parse(command.name),
            description=(
                None
                if command.description is None
                else ProjectDescription.parse(command.description)
            ),
            now=self._clock.now(),
        )
        self._repository.save(project)
        return project
