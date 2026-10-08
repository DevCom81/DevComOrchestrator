from __future__ import annotations

from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse

from devcom.entrypoints.http.cursor_presenter import (
    approval_to_dto,
    context_to_dto,
    export_to_dto,
    plan_to_dto,
    return_to_dto,
)
from devcom.entrypoints.http.deps import ContainerDep
from devcom.entrypoints.http.schemas.cursor_schemas import (
    ApprovalDto,
    CreateReturnReviewBody,
    CursorExportDto,
    CursorPlanDto,
    CursorPlanListDto,
    CursorReturnDto,
    DecideGoBody,
    IdempotencyBody,
    ImportReturnBody,
    RequestGoBody,
    ReturnContextDto,
    UpdateCursorPlanBody,
)
from devcom.entrypoints.http.schemas.tech_schemas import TechReviewDto
from devcom.entrypoints.http.tech_presenter import review_to_dto
from devcom.modules.missions.tech.cursor.application.create_plan import (
    CreateCursorPlanCommand,
)
from devcom.modules.missions.tech.cursor.application.create_return_review import (
    CreateReturnTechReviewCommand,
)
from devcom.modules.missions.tech.cursor.application.decide_go import DecideCursorGoCommand
from devcom.modules.missions.tech.cursor.application.export_plan import (
    ExportCursorPlanCommand,
)
from devcom.modules.missions.tech.cursor.application.get_plan import (
    GetCursorPlanQuery,
    ListCursorPlansQuery,
)
from devcom.modules.missions.tech.cursor.application.import_return import (
    ImportCursorReturnCommand,
)
from devcom.modules.missions.tech.cursor.application.request_go import RequestCursorGoCommand
from devcom.modules.missions.tech.cursor.application.return_context import (
    GetReturnContextQuery,
)
from devcom.modules.missions.tech.cursor.application.update_plan import (
    UpdateCursorPlanCommand,
)
from devcom.modules.missions.tech.domain.status import ExecutionMode

router = APIRouter(tags=["cursor"])


@router.post(
    "/api/tech/reviews/{review_id}/cursor-plans",
    response_model=CursorPlanDto,
    status_code=status.HTTP_201_CREATED,
)
def create_plan(review_id: str, container: ContainerDep) -> CursorPlanDto:
    plan = container.cursor.create_cursor_plan.execute(
        CreateCursorPlanCommand(review_id=review_id)
    )
    return plan_to_dto(plan)


@router.get("/api/tech/reviews/{review_id}/cursor-plans", response_model=CursorPlanListDto)
def list_plans(review_id: str, container: ContainerDep) -> CursorPlanListDto:
    items = container.cursor.list_cursor_plans.execute(
        ListCursorPlansQuery(review_id=review_id)
    )
    return CursorPlanListDto(items=[plan_to_dto(item) for item in items])


@router.get("/api/cursor/plans/{plan_id}", response_model=CursorPlanDto)
def get_plan(plan_id: str, container: ContainerDep) -> CursorPlanDto:
    plan = container.cursor.get_cursor_plan.execute(GetCursorPlanQuery(plan_id=plan_id))
    return plan_to_dto(plan)


@router.patch("/api/cursor/plans/{plan_id}", response_model=CursorPlanDto)
def update_plan(
    plan_id: str, body: UpdateCursorPlanBody, container: ContainerDep
) -> CursorPlanDto:
    plan = container.cursor.update_cursor_plan.execute(
        UpdateCursorPlanCommand(
            plan_id=plan_id,
            expected_version=body.expected_version,
            objectif=body.objectif,
            perimetre=body.perimetre,
            exclusions=body.exclusions,
            contraintes_architecture=body.contraintes_architecture,
            criteres_acceptation=body.criteres_acceptation,
            validations_attendues=body.validations_attendues,
        )
    )
    return plan_to_dto(plan)


@router.get("/api/cursor/plans/{plan_id}/preview", response_class=PlainTextResponse)
def preview_plan(plan_id: str, container: ContainerDep) -> str:
    plan = container.cursor.get_cursor_plan.execute(GetCursorPlanQuery(plan_id=plan_id))
    return plan.preview_text()


@router.post("/api/cursor/plans/{plan_id}/request-go", response_model=ApprovalDto)
def request_go(
    plan_id: str, body: RequestGoBody, container: ContainerDep
) -> ApprovalDto:
    _plan, approval = container.cursor.request_cursor_go.execute(
        RequestCursorGoCommand(
            plan_id=plan_id,
            expected_version=body.expected_version,
            idempotency_key=body.idempotency_key,
        )
    )
    return approval_to_dto(approval)


@router.post("/api/approvals/{approval_id}/decide", response_model=ApprovalDto)
def decide_go(
    approval_id: str, body: DecideGoBody, container: ContainerDep
) -> ApprovalDto:
    approval = container.cursor.decide_cursor_go.execute(
        DecideCursorGoCommand(approval_id=approval_id, grant=body.grant)
    )
    return approval_to_dto(approval)


@router.post("/api/cursor/plans/{plan_id}/export", response_model=CursorExportDto)
def export_plan(
    plan_id: str, body: IdempotencyBody, container: ContainerDep
) -> CursorExportDto:
    item = container.cursor.export_cursor_plan.execute(
        ExportCursorPlanCommand(plan_id=plan_id, idempotency_key=body.idempotency_key)
    )
    return export_to_dto(item)


@router.get("/api/cursor/exports/{export_id}", response_model=CursorExportDto)
def get_export(export_id: str, container: ContainerDep) -> CursorExportDto:
    item = container.cursor.cursor_store.get_export(export_id)
    if item is None:
        from devcom.modules.missions.tech.cursor.domain.errors import CursorNotFoundError

        raise CursorNotFoundError("export not found")
    return export_to_dto(item)


@router.get("/api/cursor/plans/{plan_id}/exports")
def list_exports(plan_id: str, container: ContainerDep) -> dict[str, Any]:
    items = container.cursor.cursor_store.list_exports(plan_id)
    return {"items": [export_to_dto(item) for item in items]}


@router.post(
    "/api/cursor/plans/{plan_id}/returns",
    response_model=CursorReturnDto,
    status_code=status.HTTP_201_CREATED,
)
def import_return(
    plan_id: str, body: ImportReturnBody, container: ContainerDep
) -> CursorReturnDto:
    item = container.cursor.import_cursor_return.execute(
        ImportCursorReturnCommand(
            plan_id=plan_id,
            export_id=body.export_id,
            report_text=body.report_text,
            diff_text=body.diff_text,
            declared_base=body.declared_base,
            declared_commit=body.declared_commit,
        )
    )
    return return_to_dto(item)


@router.get("/api/cursor/plans/{plan_id}/returns")
def list_returns(plan_id: str, container: ContainerDep) -> dict[str, Any]:
    items = container.cursor.cursor_store.list_returns(plan_id)
    return {"items": [return_to_dto(item) for item in items]}


@router.get("/api/cursor/returns/{return_id}/context", response_model=ReturnContextDto)
def return_context(return_id: str, container: ContainerDep) -> ReturnContextDto:
    raw = container.cursor.get_return_context.execute(
        GetReturnContextQuery(return_id=return_id)
    )
    return context_to_dto(raw)


@router.post(
    "/api/cursor/returns/{return_id}/tech-review",
    response_model=TechReviewDto,
    status_code=status.HTTP_201_CREATED,
)
def create_return_review(
    return_id: str, body: CreateReturnReviewBody, container: ContainerDep
) -> TechReviewDto:
    review = container.cursor.create_return_tech_review.execute(
        CreateReturnTechReviewCommand(
            return_id=return_id,
            idempotency_key=body.idempotency_key,
            execution_mode=ExecutionMode(body.execution_mode),
        )
    )
    return review_to_dto(review, container.scenario_catalog)
