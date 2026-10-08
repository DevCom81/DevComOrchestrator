from __future__ import annotations

from fastapi import APIRouter

from devcom.entrypoints.http.cursor_presenter import (
    approval_to_dto,
    execution_to_dto,
    integration_to_dto,
)
from devcom.entrypoints.http.deps import ContainerDep
from devcom.entrypoints.http.schemas.cursor_schemas import (
    ApplyIntegrateBody,
    CursorExecutionDto,
    CursorIntegrationDto,
    ExecutePreviewDto,
    IdempotencyBody,
    IntegratePreviewDto,
    RequestExecuteGoBody,
    StartExecutionBody,
)
from devcom.modules.missions.tech.cursor.application.apply_integrate import (
    ApplyIntegrateCommand,
)
from devcom.modules.missions.tech.cursor.application.cancel_execution import (
    CancelExecutionCommand,
)
from devcom.modules.missions.tech.cursor.application.request_execute_go import (
    RequestExecuteGoCommand,
)
from devcom.modules.missions.tech.cursor.application.request_integrate_go import (
    RequestIntegrateGoCommand,
)
from devcom.modules.missions.tech.cursor.application.start_execution import (
    StartExecutionCommand,
)
from devcom.modules.missions.tech.cursor.domain.errors import CursorNotFoundError

router = APIRouter(tags=["cursor-execution"])


@router.post(
    "/api/cursor/plans/{plan_id}/request-execute-go",
    response_model=ExecutePreviewDto,
)
def request_execute_go(
    plan_id: str, body: RequestExecuteGoBody, container: ContainerDep
) -> ExecutePreviewDto:
    preview, approval = container.cursor.request_execute_go.execute(
        RequestExecuteGoCommand(
            plan_id=plan_id,
            expected_version=body.expected_version,
            idempotency_key=body.idempotency_key,
            source_root=body.source_root,
            correction=body.correction,
            prior_execution_id=body.prior_execution_id,
            review_observations=body.review_observations,
        )
    )
    return ExecutePreviewDto(
        payload=preview["payload"],  # type: ignore[arg-type]
        payload_hash=str(preview["payload_hash"]),
        payload_json=str(preview["payload_json"]),
        budget_layers=preview["budget_layers"],  # type: ignore[arg-type]
        approval=approval_to_dto(approval),
    )


@router.post(
    "/api/cursor/plans/{plan_id}/executions",
    response_model=CursorExecutionDto,
)
def start_execution(
    plan_id: str, body: StartExecutionBody, container: ContainerDep
) -> CursorExecutionDto:
    item = container.cursor.start_execution.execute(
        StartExecutionCommand(
            plan_id=plan_id,
            approval_id=body.approval_id,
            idempotency_key=body.idempotency_key,
            payload_json=body.payload_json,
            payload_hash=body.payload_hash,
        )
    )
    return execution_to_dto(item)


@router.get("/api/cursor/plans/{plan_id}/executions")
def list_executions(plan_id: str, container: ContainerDep) -> dict[str, list[CursorExecutionDto]]:
    items = container.cursor.execution_store.list_for_plan(plan_id)
    return {"items": [execution_to_dto(item) for item in items]}


@router.get("/api/cursor/executions/{execution_id}", response_model=CursorExecutionDto)
def get_execution(execution_id: str, container: ContainerDep) -> CursorExecutionDto:
    item = container.cursor.execution_store.get(execution_id)
    if item is None:
        raise CursorNotFoundError("execution not found")
    return execution_to_dto(item)


@router.post(
    "/api/cursor/executions/{execution_id}/cancel",
    response_model=CursorExecutionDto,
)
def cancel_execution(execution_id: str, container: ContainerDep) -> CursorExecutionDto:
    item = container.cursor.cancel_execution.execute(
        CancelExecutionCommand(execution_id=execution_id)
    )
    return execution_to_dto(item)


@router.post(
    "/api/cursor/executions/{execution_id}/request-integrate-go",
    response_model=IntegratePreviewDto,
)
def request_integrate_go(
    execution_id: str, body: IdempotencyBody, container: ContainerDep
) -> IntegratePreviewDto:
    preview, approval = container.cursor.request_integrate_go.execute(
        RequestIntegrateGoCommand(
            execution_id=execution_id,
            idempotency_key=body.idempotency_key,
        )
    )
    return IntegratePreviewDto(preview=preview, approval=approval_to_dto(approval))


@router.post(
    "/api/cursor/executions/{execution_id}/integrate",
    response_model=CursorIntegrationDto,
)
def apply_integrate(
    execution_id: str, body: ApplyIntegrateBody, container: ContainerDep
) -> CursorIntegrationDto:
    item = container.cursor.apply_integrate.execute(
        ApplyIntegrateCommand(
            execution_id=execution_id,
            approval_id=body.approval_id,
            idempotency_key=body.idempotency_key,
            runs_root=container.cursor.runs_root,
        )
    )
    return integration_to_dto(item)
