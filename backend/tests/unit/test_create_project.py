from datetime import UTC, datetime

from devcom.modules.projects.application.create_project import (
    CreateProject,
    CreateProjectCommand,
)
from devcom.modules.projects.domain.project import Project
from devcom.shared.ids import ProjectId


class MemoryRepo:
    def __init__(self) -> None:
        self.items: dict[str, Project] = {}

    def save(self, project: Project) -> None:
        self.items[str(project.id)] = project

    def get_by_id(self, project_id: ProjectId) -> Project | None:
        return self.items.get(str(project_id))

    def list_all(self) -> list[Project]:
        return list(self.items.values())


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 7, 10, 0, tzinfo=UTC)


def test_create_project_persists() -> None:
    repo = MemoryRepo()
    use_case = CreateProject(repo, FixedClock())
    project = use_case.execute(
        CreateProjectCommand(name="  Lot0  ", description="  Fondation  ")
    )
    assert project.name.value == "Lot0"
    assert str(project.id) in repo.items
