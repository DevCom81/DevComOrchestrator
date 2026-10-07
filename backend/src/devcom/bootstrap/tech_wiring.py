from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from devcom.bootstrap.settings import Settings
from devcom.modules.missions.domain.capability import CapabilityRegistry
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.ports.project_existence import ProjectExistencePort
from devcom.modules.missions.tech.adapters.blocking_policy_loader import load_blocking_policy
from devcom.modules.missions.tech.adapters.project_snapshot_adapter import (
    SqlProjectSnapshotAdapter,
)
from devcom.modules.missions.tech.adapters.scenario_catalog import (
    ScenarioCatalog,
    load_scenario_catalog,
)
from devcom.modules.missions.tech.adapters.sqlalchemy_tech_repository import (
    SqlAlchemyTechReviewRepository,
    SqlIdempotencyStore,
)
from devcom.modules.missions.tech.application.create_review import CreateTechReview
from devcom.modules.missions.tech.application.decide_review import DecideTechReview
from devcom.modules.missions.tech.application.get_review import GetTechReview
from devcom.modules.missions.tech.application.list_reviews import ListTechReviews
from devcom.modules.missions.tech.application.list_scenarios import ListTechScenarios
from devcom.modules.missions.tech.application.run_pipeline import RunTechPipeline
from devcom.modules.missions.tech.application.select_scenario import SelectScenario
from devcom.shared.time import Clock


@dataclass(slots=True)
class TechServices:
    scenario_catalog: ScenarioCatalog
    list_tech_scenarios: ListTechScenarios
    create_tech_review: CreateTechReview
    get_tech_review: GetTechReview
    list_tech_reviews: ListTechReviews
    select_tech_scenario: SelectScenario
    run_tech_pipeline: RunTechPipeline
    decide_tech_review: DecideTechReview


def build_tech_services(
    settings: Settings,
    session_factory: sessionmaker[Session],
    project_existence: ProjectExistencePort,
    registry: CapabilityRegistry,
    policy: PermissionPolicy,
    clock: Clock,
) -> TechServices:
    repo = SqlAlchemyTechReviewRepository(session_factory)
    idem = SqlIdempotencyStore(session_factory)
    catalog = load_scenario_catalog(settings.tech_scenarios_index_path)
    blocking = load_blocking_policy(settings.tech_blocking_policy_path)
    snapshots = SqlProjectSnapshotAdapter(session_factory)
    return TechServices(
        scenario_catalog=catalog,
        list_tech_scenarios=ListTechScenarios(catalog),
        create_tech_review=CreateTechReview(
            repo, project_existence, catalog, policy, idem, clock
        ),
        get_tech_review=GetTechReview(repo),
        list_tech_reviews=ListTechReviews(repo),
        select_tech_scenario=SelectScenario(repo, catalog, snapshots, clock),
        run_tech_pipeline=RunTechPipeline(
            repo, catalog, registry, policy, blocking, idem, clock
        ),
        decide_tech_review=DecideTechReview(repo, policy, idem, clock),
    )
