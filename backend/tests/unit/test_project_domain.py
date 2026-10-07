from datetime import UTC, datetime

import pytest

from devcom.modules.projects.domain.errors import ProjectValidationError
from devcom.modules.projects.domain.project import (
    Project,
    ProjectDescription,
    ProjectName,
)


def test_name_trims_and_rejects_empty() -> None:
    assert ProjectName.parse("  Alpha  ").value == "Alpha"
    with pytest.raises(ProjectValidationError):
        ProjectName.parse("   ")


def test_name_rejects_overlong() -> None:
    with pytest.raises(ProjectValidationError):
        ProjectName.parse("x" * 81)


def test_description_bounds() -> None:
    assert ProjectDescription.parse("  hello  ").value == "hello"
    with pytest.raises(ProjectValidationError):
        ProjectDescription.parse("x" * 2001)


def test_create_and_update_project() -> None:
    now = datetime(2026, 10, 7, 8, 0, tzinfo=UTC)
    project = Project.create(
        name=ProjectName.parse("Demo"),
        description=ProjectDescription.parse("First"),
        now=now,
    )
    later = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
    project.update(
        name=ProjectName.parse("Demo 2"),
        description=None,
        now=later,
    )
    assert project.name.value == "Demo 2"
    assert project.description.value == "First"
    assert project.updated_at == later


def test_update_requires_field() -> None:
    now = datetime(2026, 10, 7, 8, 0, tzinfo=UTC)
    project = Project.create(
        name=ProjectName.parse("Demo"),
        description=ProjectDescription.parse("First"),
        now=now,
    )
    with pytest.raises(ProjectValidationError):
        project.update(name=None, description=None, now=now)
