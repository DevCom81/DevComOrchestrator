from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.projects.domain.project import (
    Project,
    ProjectDescription,
    ProjectName,
)
from devcom.modules.projects.ports.project_repository import ProjectRepository
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class CreateProjectCommand:
    name: str
    description: str


class CreateProject:
    def __init__(self, repository: ProjectRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, command: CreateProjectCommand) -> Project:
        project = Project.create(
            name=ProjectName.parse(command.name),
            description=ProjectDescription.parse(command.description),
            now=self._clock.now(),
        )
        self._repository.save(project)
        return project
