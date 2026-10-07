from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.missions.tech.domain.artifacts import ContextSnapshot
from devcom.modules.missions.tech.domain.errors import TechNotFoundError
from devcom.modules.projects.adapters.sqlalchemy_models import ProjectRow


class SqlProjectSnapshotAdapter:
    """Read-only project freeze — not the projects repository API."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def capture(self, project_id: str, captured_at: str) -> ContextSnapshot:
        with self._session_factory() as session:
            row = session.get(ProjectRow, project_id)
            if row is None:
                raise TechNotFoundError(f"project {project_id} not found")
            return ContextSnapshot(
                project_id=row.id,
                project_name=row.name,
                project_description=row.description,
                project_updated_at=_as_utc(row.updated_at).isoformat(),
                captured_at=captured_at,
            )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
