from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from devcom.bootstrap.settings import Settings
from devcom.modules.agents.adapters.static_agent_catalog import StaticAgentCatalog
from devcom.modules.agents.application.list_agents import ListAgents
from devcom.modules.missions.adapters.json_contracts import (
    load_capability_registry,
    load_demo_dispatch_rules,
    load_permission_policy,
)
from devcom.modules.missions.adapters.project_existence_adapter import (
    SqlProjectExistenceAdapter,
)
from devcom.modules.missions.adapters.sqlalchemy_mission_repository import (
    SqlAlchemyMissionRepository,
)
from devcom.modules.missions.application.answer_clarification import AnswerClarification
from devcom.modules.missions.application.create_mission import CreateMission
from devcom.modules.missions.application.demo_dispatcher import DemoDispatcher
from devcom.modules.missions.application.get_mission import GetMission
from devcom.modules.missions.application.list_missions import ListMissions
from devcom.modules.missions.application.orchestrator import MissionOrchestrator
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
    demo_dispatcher: DemoDispatcher
    create_mission: CreateMission
    get_mission: GetMission
    list_missions: ListMissions
    answer_clarification: AnswerClarification


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
    project_repository = SqlAlchemyProjectRepository(session_factory)
    mission_repository = SqlAlchemyMissionRepository(session_factory)
    project_existence = SqlProjectExistenceAdapter(session_factory)
    clock = SystemClock()
    catalog = StaticAgentCatalog(settings.agents_contracts_dir)
    registry = load_capability_registry(settings.capabilities_registry_path)
    policy = load_permission_policy(settings.permissions_policy_path)
    dispatch_rules = load_demo_dispatch_rules(settings.dispatch_rules_path)
    dispatcher = DemoDispatcher(dispatch_rules)
    orchestrator = MissionOrchestrator(dispatcher, registry, policy)
    return ApplicationContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        create_project=CreateProject(project_repository, clock),
        get_project=GetProject(project_repository),
        list_projects=ListProjects(project_repository),
        update_project=UpdateProject(project_repository, clock),
        list_agents=ListAgents(catalog),
        demo_dispatcher=dispatcher,
        create_mission=CreateMission(
            mission_repository,
            project_existence,
            orchestrator,
            clock,
        ),
        get_mission=GetMission(mission_repository),
        list_missions=ListMissions(mission_repository),
        answer_clarification=AnswerClarification(
            mission_repository,
            orchestrator,
            clock,
        ),
    )
