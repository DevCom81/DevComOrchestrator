from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from devcom.bootstrap.settings import Settings
from devcom.modules.approvals.adapters.sqlalchemy_store import SqlAlchemyApprovalStore
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.create_review import CreateTechReview
from devcom.modules.missions.tech.cursor.adapters.execution_budget import ExecutionBudgetGate
from devcom.modules.missions.tech.cursor.adapters.fake_cursor_agent import FakeCursorAgent
from devcom.modules.missions.tech.cursor.adapters.real_cursor_agent import RealCursorAgent
from devcom.modules.missions.tech.cursor.adapters.return_artifacts import (
    CursorReturnArtifactStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_execution_store import (
    SqlAlchemyExecutionStore,
)
from devcom.modules.missions.tech.cursor.application.apply_integrate import ApplyIntegrate
from devcom.modules.missions.tech.cursor.application.cancel_execution import CancelExecution
from devcom.modules.missions.tech.cursor.application.create_plan import CreateCursorPlan
from devcom.modules.missions.tech.cursor.application.create_return_review import (
    CreateReturnTechReview,
)
from devcom.modules.missions.tech.cursor.application.decide_go import DecideCursorGo
from devcom.modules.missions.tech.cursor.application.export_plan import ExportCursorPlan
from devcom.modules.missions.tech.cursor.application.get_plan import (
    GetCursorPlan,
    ListCursorPlans,
)
from devcom.modules.missions.tech.cursor.application.import_return import ImportCursorReturn
from devcom.modules.missions.tech.cursor.application.request_execute_go import RequestExecuteGo
from devcom.modules.missions.tech.cursor.application.request_go import RequestCursorGo
from devcom.modules.missions.tech.cursor.application.request_integrate_go import (
    RequestIntegrateGo,
)
from devcom.modules.missions.tech.cursor.application.return_context import GetReturnContext
from devcom.modules.missions.tech.cursor.application.start_execution import StartExecution
from devcom.modules.missions.tech.cursor.application.update_plan import UpdateCursorPlan
from devcom.modules.missions.tech.cursor.domain.errors import CursorConflictError
from devcom.modules.missions.tech.cursor.ports.cursor_agent_port import CursorAgentPort
from devcom.modules.missions.tech.ports.code_snapshot_port import CodeSnapshotPort
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
from devcom.shared.time import Clock


@dataclass(slots=True)
class CursorServices:
    create_cursor_plan: CreateCursorPlan
    update_cursor_plan: UpdateCursorPlan
    get_cursor_plan: GetCursorPlan
    list_cursor_plans: ListCursorPlans
    request_cursor_go: RequestCursorGo
    decide_cursor_go: DecideCursorGo
    export_cursor_plan: ExportCursorPlan
    import_cursor_return: ImportCursorReturn
    get_return_context: GetReturnContext
    create_return_tech_review: CreateReturnTechReview
    request_execute_go: RequestExecuteGo
    start_execution: StartExecution
    cancel_execution: CancelExecution
    request_integrate_go: RequestIntegrateGo
    apply_integrate: ApplyIntegrate
    cursor_store: SqlAlchemyCursorStore
    execution_store: SqlAlchemyExecutionStore
    approval_store: SqlAlchemyApprovalStore
    cursor_agent: CursorAgentPort
    runs_root: Path


def build_cursor_agent(settings: Settings) -> CursorAgentPort:
    if settings.cursor_adapter == "fake":
        if settings.mode == "real":
            raise CursorConflictError("real mode cannot use fake cursor adapter")
        return FakeCursorAgent()
    key = (settings.cursor_api_key or "").strip()
    if not key:
        raise CursorConflictError(
            "CURSOR_API_KEY missing — configure backend/.env or environment "
            "(value never logged); Fake is not substituted in real mode"
        )
    return RealCursorAgent(api_key=key)


def build_cursor_services(
    *,
    sessions: sessionmaker[Session],
    settings: Settings,
    reviews: TechReviewRepository,
    create_review: CreateTechReview,
    policy: PermissionPolicy,
    clock: Clock,
    code_snapshots: CodeSnapshotPort | None,
) -> CursorServices:
    plans = SqlAlchemyCursorStore(sessions)
    approvals = SqlAlchemyApprovalStore(sessions)
    executions = SqlAlchemyExecutionStore(sessions)
    artifacts = CursorReturnArtifactStore(settings.data_dir)
    agent = build_cursor_agent(settings)
    runs_root = settings.data_dir / "cursor_runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    budget = ExecutionBudgetGate(
        sessions, monthly_cap=settings.monthly_budget_eur_micros
    )
    return CursorServices(
        create_cursor_plan=CreateCursorPlan(
            reviews=reviews, plans=plans, policy=policy, clock=clock
        ),
        update_cursor_plan=UpdateCursorPlan(
            plans=plans, approvals=approvals, policy=policy, clock=clock
        ),
        get_cursor_plan=GetCursorPlan(plans),
        list_cursor_plans=ListCursorPlans(plans),
        request_cursor_go=RequestCursorGo(
            plans=plans, approvals=approvals, policy=policy, clock=clock
        ),
        decide_cursor_go=DecideCursorGo(
            plans=plans, approvals=approvals, policy=policy, clock=clock
        ),
        export_cursor_plan=ExportCursorPlan(
            sessions=sessions, plans=plans, policy=policy, clock=clock
        ),
        import_cursor_return=ImportCursorReturn(
            plans=plans,
            artifacts=artifacts,
            snapshots=code_snapshots,
            policy=policy,
            clock=clock,
        ),
        get_return_context=GetReturnContext(plans, artifacts),
        create_return_tech_review=CreateReturnTechReview(
            plans=plans,
            artifacts=artifacts,
            create_review=create_review,
            policy=policy,
        ),
        request_execute_go=RequestExecuteGo(
            plans=plans,
            executions=executions,
            approvals=approvals,
            policy=policy,
            clock=clock,
        ),
        start_execution=StartExecution(
            plans=plans,
            executions=executions,
            approvals=approvals,
            agent=agent,
            budget=budget,
            artifacts=artifacts,
            runs_root=runs_root,
            policy=policy,
            clock=clock,
        ),
        cancel_execution=CancelExecution(
            executions=executions, agent=agent, policy=policy, clock=clock
        ),
        request_integrate_go=RequestIntegrateGo(
            executions=executions, approvals=approvals, policy=policy, clock=clock
        ),
        apply_integrate=ApplyIntegrate(
            executions=executions, approvals=approvals, policy=policy, clock=clock
        ),
        cursor_store=plans,
        execution_store=executions,
        approval_store=approvals,
        cursor_agent=agent,
        runs_root=runs_root,
    )
