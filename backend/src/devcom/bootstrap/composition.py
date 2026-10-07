from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from devcom.bootstrap.settings import Settings
from devcom.modules.agents.adapters.static_agent_catalog import StaticAgentCatalog
from devcom.modules.agents.application.list_agents import ListAgents
from devcom.modules.projects.adapters.sqlalchemy_project_repository import (
    SqlAlchemyProjectRepository,
)
from devcom.modules.projects.application.create_project import CreateProject
from devcom.modules.projects.application.get_project import GetProject
from devcom.modules.projects.application.list_projects import ListProjects
from devcom.modules.projects.application.update_project import UpdateProject
from devcom.shared.time import SystemClock


@dataclass(slots=True)
class ApplicationContainer:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    create_project: CreateProject
    get_project: GetProject
    list_projects: ListProjects
    update_project: UpdateProject
    list_agents: ListAgents


def build_engine(database_path: Path) -> Engine:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{database_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: object, _connection_record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def build_container(settings: Settings) -> ApplicationContainer:
    engine = build_engine(settings.database_path)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    repository = SqlAlchemyProjectRepository(session_factory)
    clock = SystemClock()
    catalog = StaticAgentCatalog(settings.contracts_dir)
    return ApplicationContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        create_project=CreateProject(repository, clock),
        get_project=GetProject(repository),
        list_projects=ListProjects(repository),
        update_project=UpdateProject(repository, clock),
        list_agents=ListAgents(catalog),
    )
