from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.approvals.adapters.sqlalchemy_store import SqlAlchemyApprovalStore
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.create_review import CreateTechReview
from devcom.modules.missions.tech.cursor.adapters.return_artifacts import (
    CursorReturnArtifactStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
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
from devcom.modules.missions.tech.cursor.application.request_go import RequestCursorGo
from devcom.modules.missions.tech.cursor.application.return_context import GetReturnContext
from devcom.modules.missions.tech.cursor.application.update_plan import UpdateCursorPlan
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
    cursor_store: SqlAlchemyCursorStore
    approval_store: SqlAlchemyApprovalStore


def build_cursor_services(
    *,
    sessions: sessionmaker[Session],
    data_dir: Path,
    reviews: TechReviewRepository,
    create_review: CreateTechReview,
    policy: PermissionPolicy,
    clock: Clock,
    code_snapshots: CodeSnapshotPort | None,
) -> CursorServices:
    plans = SqlAlchemyCursorStore(sessions)
    approvals = SqlAlchemyApprovalStore(sessions)
    artifacts = CursorReturnArtifactStore(data_dir)
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
        cursor_store=plans,
        approval_store=approvals,
    )
