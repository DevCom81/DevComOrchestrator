from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from devcom.bootstrap.code_context_wiring import CodeContextServices, build_code_context_services
from devcom.bootstrap.settings import Settings
from devcom.bootstrap.tech_wiring import TechServices, build_tech_services
from devcom.modules.agents.adapters.static_agent_catalog import StaticAgentCatalog
from devcom.modules.agents.application.list_agents import ListAgents
from devcom.modules.billing.adapters.sqlalchemy_ledger import SqlAlchemyBudgetLedger
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
from devcom.modules.missions.tech.adapters.scenario_catalog import ScenarioCatalog
from devcom.modules.missions.tech.adapters.sqlalchemy_steps import SqlAlchemyStepStore
from devcom.modules.missions.tech.application.create_review import CreateTechReview
from devcom.modules.missions.tech.application.decide_review import DecideTechReview
from devcom.modules.missions.tech.application.get_review import GetTechReview
from devcom.modules.missions.tech.application.list_reviews import ListTechReviews
from devcom.modules.missions.tech.application.list_scenarios import ListTechScenarios
from devcom.modules.missions.tech.application.run_pipeline import RunTechPipeline
from devcom.modules.missions.tech.application.select_scenario import SelectScenario
from devcom.modules.missions.tech.application.start_real_review import StartRealTechReview
from devcom.modules.missions.tech.ports.llm_completion import LlmCompletionPort
from devcom.modules.projects.adapters.sqlalchemy_project_repository import (
    SqlAlchemyProjectRepository,
)
from devcom.modules.projects.application.attach_source_root import AttachSourceRoot
from devcom.modules.projects.application.browse_source_tree import BrowseSourceTree
from devcom.modules.projects.application.create_code_preview import CreateCodePreview
from devcom.modules.projects.application.create_project import CreateProject
from devcom.modules.projects.application.detach_source_root import DetachSourceRoot
from devcom.modules.projects.application.freeze_code_snapshot import (
    FreezeCodeSnapshot,
    GetCodeSnapshot,
)
from devcom.modules.projects.application.get_project import GetProject
from devcom.modules.projects.application.get_source_root import GetSourceRoot
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
    attach_source_root: AttachSourceRoot
    detach_source_root: DetachSourceRoot
    get_source_root: GetSourceRoot
    browse_source_tree: BrowseSourceTree
    create_code_preview: CreateCodePreview
    freeze_code_snapshot: FreezeCodeSnapshot
    get_code_snapshot: GetCodeSnapshot
    list_agents: ListAgents
    demo_dispatcher: DemoDispatcher
    create_mission: CreateMission
    get_mission: GetMission
    list_missions: ListMissions
    answer_clarification: AnswerClarification
    scenario_catalog: ScenarioCatalog
    list_tech_scenarios: ListTechScenarios
    create_tech_review: CreateTechReview
    get_tech_review: GetTechReview
    list_tech_reviews: ListTechReviews
    select_tech_scenario: SelectScenario
    run_tech_pipeline: RunTechPipeline
    start_real_tech_review: StartRealTechReview
    decide_tech_review: DecideTechReview
    budget_ledger: SqlAlchemyBudgetLedger
    step_store: SqlAlchemyStepStore
    openai_key_configured: bool
    llm: LlmCompletionPort


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
    sessions = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    clock = SystemClock()
    projects = SqlAlchemyProjectRepository(sessions)
    missions = SqlAlchemyMissionRepository(sessions)
    existence = SqlProjectExistenceAdapter(sessions)
    agents = StaticAgentCatalog(settings.agents_contracts_dir)
    registry = load_capability_registry(settings.capabilities_registry_path)
    policy = load_permission_policy(settings.permissions_policy_path)
    dispatcher = DemoDispatcher(load_demo_dispatch_rules(settings.dispatch_rules_path))
    orchestrator = MissionOrchestrator(dispatcher, registry, policy)
    code_ctx = build_code_context_services(settings, sessions, clock)
    tech = build_tech_services(
        settings,
        sessions,
        existence,
        registry,
        policy,
        clock,
        code_snapshots=code_ctx.code_snapshot_port,
    )
    return _container(
        settings,
        engine,
        sessions,
        projects,
        missions,
        existence,
        agents,
        dispatcher,
        orchestrator,
        clock,
        tech,
        code_ctx,
    )


def _container(
    settings: Settings,
    engine: Engine,
    sessions: sessionmaker[Session],
    projects: SqlAlchemyProjectRepository,
    missions: SqlAlchemyMissionRepository,
    existence: SqlProjectExistenceAdapter,
    agents: StaticAgentCatalog,
    dispatcher: DemoDispatcher,
    orchestrator: MissionOrchestrator,
    clock: SystemClock,
    tech: TechServices,
    code_ctx: CodeContextServices,
) -> ApplicationContainer:
    return ApplicationContainer(
        settings=settings,
        engine=engine,
        session_factory=sessions,
        create_project=CreateProject(projects, clock),
        get_project=GetProject(projects),
        list_projects=ListProjects(projects),
        update_project=UpdateProject(projects, clock),
        attach_source_root=code_ctx.attach_source_root,
        detach_source_root=code_ctx.detach_source_root,
        get_source_root=code_ctx.get_source_root,
        browse_source_tree=code_ctx.browse_source_tree,
        create_code_preview=code_ctx.create_code_preview,
        freeze_code_snapshot=code_ctx.freeze_code_snapshot,
        get_code_snapshot=code_ctx.get_code_snapshot,
        list_agents=ListAgents(agents),
        demo_dispatcher=dispatcher,
        create_mission=CreateMission(missions, existence, orchestrator, clock),
        get_mission=GetMission(missions),
        list_missions=ListMissions(missions),
        answer_clarification=AnswerClarification(missions, orchestrator, clock),
        scenario_catalog=tech.scenario_catalog,
        list_tech_scenarios=tech.list_tech_scenarios,
        create_tech_review=tech.create_tech_review,
        get_tech_review=tech.get_tech_review,
        list_tech_reviews=tech.list_tech_reviews,
        select_tech_scenario=tech.select_tech_scenario,
        run_tech_pipeline=tech.run_tech_pipeline,
        start_real_tech_review=tech.start_real_tech_review,
        decide_tech_review=tech.decide_tech_review,
        budget_ledger=tech.budget_ledger,
        step_store=tech.step_store,
        openai_key_configured=tech.openai_key_configured,
        llm=tech.llm,
    )
