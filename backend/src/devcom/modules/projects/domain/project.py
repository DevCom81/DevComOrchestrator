from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from devcom.modules.projects.domain.errors import ProjectValidationError
from devcom.shared.ids import ProjectId

NAME_MIN_LENGTH = 1
NAME_MAX_LENGTH = 80
DESCRIPTION_MIN_LENGTH = 1
DESCRIPTION_MAX_LENGTH = 2000


@dataclass(frozen=True, slots=True)
class ProjectName:
    value: str

    @classmethod
    def parse(cls, raw: str) -> ProjectName:
        trimmed = raw.strip()
        if not (NAME_MIN_LENGTH <= len(trimmed) <= NAME_MAX_LENGTH):
            raise ProjectValidationError(
                f"name must be {NAME_MIN_LENGTH} to {NAME_MAX_LENGTH} characters after trim"
            )
        return cls(trimmed)


@dataclass(frozen=True, slots=True)
class ProjectDescription:
    value: str

    @classmethod
    def parse(cls, raw: str) -> ProjectDescription:
        trimmed = raw.strip()
        if not (DESCRIPTION_MIN_LENGTH <= len(trimmed) <= DESCRIPTION_MAX_LENGTH):
            raise ProjectValidationError(
                "description must be "
                f"{DESCRIPTION_MIN_LENGTH} to {DESCRIPTION_MAX_LENGTH} characters after trim"
            )
        return cls(trimmed)


@dataclass(slots=True)
class Project:
    id: ProjectId
    name: ProjectName
    description: ProjectDescription
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        name: ProjectName,
        description: ProjectDescription,
        now: datetime,
        project_id: ProjectId | None = None,
    ) -> Project:
        stamp = _require_utc(now)
        return cls(
            id=project_id or ProjectId.new(),
            name=name,
            description=description,
            created_at=stamp,
            updated_at=stamp,
        )

    def update(
        self,
        *,
        name: ProjectName | None,
        description: ProjectDescription | None,
        now: datetime,
    ) -> None:
        if name is None and description is None:
            raise ProjectValidationError("at least one of name or description is required")
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        self.updated_at = _require_utc(now)


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ProjectValidationError("timestamps must be timezone-aware UTC")
    return value.astimezone(UTC)
