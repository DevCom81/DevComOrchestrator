from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.projects.adapters.sqlalchemy_models import ProjectRow


class SqlProjectExistenceAdapter:
    """Read-only existence check — not the projects module repository."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def exists(self, project_id: str) -> bool:
        with self._session_factory() as session:
            value = session.scalar(select(ProjectRow.id).where(ProjectRow.id == project_id))
            return value is not None
