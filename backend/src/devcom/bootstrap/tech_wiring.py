from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from devcom.bootstrap.settings import Settings
from devcom.modules.billing.adapters.rate_tables import (
    FxTable,
    OpenAiRateTable,
    load_fx_table,
    load_openai_rates,
)
from devcom.modules.billing.adapters.sqlalchemy_ledger import SqlAlchemyBudgetLedger
from devcom.modules.missions.domain.capability import CapabilityRegistry
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.ports.project_existence import ProjectExistencePort
from devcom.modules.missions.tech.adapters.blocking_policy_loader import load_blocking_policy
from devcom.modules.missions.tech.adapters.fake_llm_adapter import FakeLlmAdapter
from devcom.modules.missions.tech.adapters.openai_responses_adapter import OpenAIResponsesAdapter
from devcom.modules.missions.tech.adapters.project_snapshot_adapter import (
    SqlProjectSnapshotAdapter,
)
from devcom.modules.missions.tech.adapters.scenario_catalog import (
    ScenarioCatalog,
    load_scenario_catalog,
)
from devcom.modules.missions.tech.adapters.sqlalchemy_steps import SqlAlchemyStepStore
from devcom.modules.missions.tech.adapters.sqlalchemy_tech_repository import (
    SqlAlchemyTechReviewRepository,
    SqlIdempotencyStore,
)
from devcom.modules.missions.tech.application.create_review import CreateTechReview
from devcom.modules.missions.tech.application.decide_review import DecideTechReview
from devcom.modules.missions.tech.application.get_review import GetTechReview
from devcom.modules.missions.tech.application.list_reviews import ListTechReviews
from devcom.modules.missions.tech.application.list_scenarios import ListTechScenarios
from devcom.modules.missions.tech.application.prepare_real_review import PrepareRealReview
from devcom.modules.missions.tech.application.prompt_loader import PromptBundle
from devcom.modules.missions.tech.application.real_executor import RealPipelineExecutor
from devcom.modules.missions.tech.application.reconcile_real import (
    reconcile_interrupted_real_pipeline,
)
from devcom.modules.missions.tech.application.run_pipeline import RunTechPipeline
from devcom.modules.missions.tech.application.select_scenario import SelectScenario
from devcom.modules.missions.tech.application.start_real_review import StartRealTechReview
from devcom.modules.missions.tech.application.supervised_runner import SupervisedRealRunner
from devcom.modules.missions.tech.domain.blocking import BlockingPolicy
from devcom.modules.missions.tech.ports.idempotency_store import IdempotencyStore
from devcom.modules.missions.tech.ports.llm_completion import LlmCompletionPort
from devcom.modules.missions.tech.ports.project_snapshot import ProjectSnapshotPort
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
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
    start_real_tech_review: StartRealTechReview
    decide_tech_review: DecideTechReview
    budget_ledger: SqlAlchemyBudgetLedger
    step_store: SqlAlchemyStepStore
    llm: LlmCompletionPort
    openai_key_configured: bool
    runner: SupervisedRealRunner


@dataclass(slots=True)
class _TechCore:
    repo: TechReviewRepository
    idem: IdempotencyStore
    catalog: ScenarioCatalog
    blocking: BlockingPolicy
    snapshots: ProjectSnapshotPort
    steps: SqlAlchemyStepStore
    ledger: SqlAlchemyBudgetLedger
    rates: OpenAiRateTable
    fx: FxTable
    prompts: PromptBundle
    prepare: PrepareRealReview


def build_tech_services(
    settings: Settings,
    session_factory: sessionmaker[Session],
    project_existence: ProjectExistencePort,
    registry: CapabilityRegistry,
    policy: PermissionPolicy,
    clock: Clock,
) -> TechServices:
    core = _build_core(settings, session_factory, clock)
    llm = FakeLlmAdapter() if settings.llm_adapter == "fake" else OpenAIResponsesAdapter()
    executor = RealPipelineExecutor(
        repository=core.repo,
        steps=core.steps,
        ledger=core.ledger,
        llm=llm,
        prompts=core.prompts,
        registry=registry,
        policy=policy,
        blocking=core.blocking,
        rates=core.rates,
        fx=core.fx,
        clock=clock,
        apply_regional=True,
    )
    runner = SupervisedRealRunner(executor.run)
    reconcile_interrupted_real_pipeline(
        session_factory=session_factory,
        steps=core.steps,
        ledger=core.ledger,
        clock=clock,
    )
    return _assemble(core, llm, runner, project_existence, registry, policy, clock, settings)


def _build_core(
    settings: Settings,
    sessions: sessionmaker[Session],
    clock: Clock,
) -> _TechCore:
    snapshots = SqlProjectSnapshotAdapter(sessions)
    return _TechCore(
        repo=SqlAlchemyTechReviewRepository(sessions),
        idem=SqlIdempotencyStore(sessions),
        catalog=load_scenario_catalog(settings.tech_scenarios_index_path),
        blocking=load_blocking_policy(settings.tech_blocking_policy_path),
        snapshots=snapshots,
        steps=SqlAlchemyStepStore(sessions),
        ledger=SqlAlchemyBudgetLedger(sessions, settings.monthly_budget_eur_micros),
        rates=load_openai_rates(settings.openai_rates_path),
        fx=load_fx_table(settings.fx_path),
        prompts=PromptBundle(settings.tech_prompts_root),
        prepare=PrepareRealReview(
            snapshots=snapshots,
            bounds_path=settings.tech_call_bounds_path,
            rates_path=settings.openai_rates_path,
            fx_path=settings.fx_path,
            review_cap_eur_micros=settings.review_budget_eur_micros,
            real_mode_enabled=settings.real_mode_enabled,
            clock=clock,
        ),
    )


def _assemble(
    core: _TechCore,
    llm: LlmCompletionPort,
    runner: SupervisedRealRunner,
    project_existence: ProjectExistencePort,
    registry: CapabilityRegistry,
    policy: PermissionPolicy,
    clock: Clock,
    settings: Settings,
) -> TechServices:
    key_present = bool(os.environ.get("OPENAI_API_KEY"))
    return TechServices(
        scenario_catalog=core.catalog,
        list_tech_scenarios=ListTechScenarios(core.catalog),
        create_tech_review=CreateTechReview(
            core.repo,
            project_existence,
            core.catalog,
            policy,
            core.idem,
            clock,
            core.prepare,
        ),
        get_tech_review=GetTechReview(core.repo),
        list_tech_reviews=ListTechReviews(core.repo),
        select_tech_scenario=SelectScenario(core.repo, core.catalog, core.snapshots, clock),
        run_tech_pipeline=RunTechPipeline(
            core.repo, core.catalog, registry, policy, core.blocking, core.idem, clock
        ),
        start_real_tech_review=StartRealTechReview(
            repository=core.repo,
            steps=core.steps,
            ledger=core.ledger,
            runner=runner,
            policy=policy,
            idempotency=core.idem,
            rates=core.rates,
            fx=core.fx,
            real_mode_enabled=settings.real_mode_enabled,
            openai_configured=key_present or settings.llm_adapter == "fake",
            clock=clock,
        ),
        decide_tech_review=DecideTechReview(core.repo, policy, core.idem, clock),
        budget_ledger=core.ledger,
        step_store=core.steps,
        llm=llm,
        openai_key_configured=key_present,
        runner=runner,
    )
