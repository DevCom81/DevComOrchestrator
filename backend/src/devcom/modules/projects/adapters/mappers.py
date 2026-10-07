from __future__ import annotations

from datetime import UTC, datetime

from devcom.modules.projects.adapters.sqlalchemy_models import ProjectRow
from devcom.modules.projects.domain.project import (
    Project,
    ProjectDescription,
    ProjectName,
)
from devcom.shared.ids import ProjectId


def row_to_project(row: ProjectRow) -> Project:
    return Project(
        id=ProjectId(row.id),
        name=ProjectName(row.name),
        description=ProjectDescription(row.description),
        created_at=_as_utc(row.created_at),
        updated_at=_as_utc(row.updated_at),
    )


def apply_project_to_row(project: Project, row: ProjectRow) -> None:
    row.id = str(project.id)
    row.name = project.name.value
    row.description = project.description.value
    row.created_at = project.created_at
    row.updated_at = project.updated_at


def project_to_new_row(project: Project) -> ProjectRow:
    return ProjectRow(
        id=str(project.id),
        name=project.name.value,
        description=project.description.value,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
