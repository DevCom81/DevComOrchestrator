from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.projects.adapters.mappers import (
    apply_project_to_row,
    project_to_new_row,
    row_to_project,
)
from devcom.modules.projects.adapters.sqlalchemy_models import ProjectRow
from devcom.modules.projects.domain.project import Project
from devcom.shared.ids import ProjectId


class SqlAlchemyProjectRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, project: Project) -> None:
        with self._session_factory() as session:
            row = session.get(ProjectRow, str(project.id))
            if row is None:
                session.add(project_to_new_row(project))
            else:
                apply_project_to_row(project, row)
            session.commit()

    def get_by_id(self, project_id: ProjectId) -> Project | None:
        with self._session_factory() as session:
            row = session.get(ProjectRow, str(project_id))
            if row is None:
                return None
            return row_to_project(row)

    def list_all(self) -> list[Project]:
        with self._session_factory() as session:
            statement = select(ProjectRow).order_by(ProjectRow.updated_at.desc())
            rows = session.scalars(statement).all()
            return [row_to_project(row) for row in rows]
