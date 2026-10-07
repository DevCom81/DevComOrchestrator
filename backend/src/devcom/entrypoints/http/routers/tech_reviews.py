from __future__ import annotations

from fastapi import APIRouter, Query, status

from devcom.entrypoints.http.deps import ContainerDep
from devcom.entrypoints.http.schemas.tech_schemas import (
    BudgetSummaryDto,
    CreateTechReviewBody,
    DecideTechReviewBody,
    RunTechPipelineBody,
    ScenarioDto,
    ScenarioListDto,
    SelectScenarioBody,
    TechReviewDto,
    TechReviewListDto,
)
from devcom.entrypoints.http.tech_presenter import review_to_dto
from devcom.modules.billing.domain.period import budget_month_id
from devcom.modules.missions.tech.application.create_review import CreateTechReviewCommand
from devcom.modules.missions.tech.application.decide_review import DecideTechReviewCommand
from devcom.modules.missions.tech.application.get_review import GetTechReviewQuery
from devcom.modules.missions.tech.application.list_reviews import ListTechReviewsQuery
from devcom.modules.missions.tech.application.run_pipeline import RunTechPipelineCommand
from devcom.modules.missions.tech.application.select_scenario import SelectScenarioCommand
from devcom.modules.missions.tech.application.start_real_review import (
    StartRealTechReviewCommand,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import ExecutionMode
from devcom.shared.time import SystemClock

router = APIRouter(tags=["tech"])


@router.get("/api/tech/scenarios", response_model=ScenarioListDto)
def list_scenarios(container: ContainerDep) -> ScenarioListDto:
    items, disclaimer = container.list_tech_scenarios.execute()
    return ScenarioListDto(
        items=[ScenarioDto(id=item.id, label=item.label) for item in items],
        disclaimer=disclaimer,
    )


@router.get("/api/budget/summary", response_model=BudgetSummaryDto)
def budget_summary(container: ContainerDep) -> BudgetSummaryDto:
    month_id = budget_month_id(SystemClock().now())
    raw = container.budget_ledger.summary(month_id)
    return BudgetSummaryDto(
        month_id=str(raw["month_id"]),
        cap_eur_micros=int(raw["cap_eur_micros"]),
        confirmed_eur_micros=int(raw["confirmed_eur_micros"]),
        reserved_eur_micros=int(raw["reserved_eur_micros"]),
        uncertain_eur_micros=int(raw["uncertain_eur_micros"]),
    )


@router.get("/api/tech/reviews", response_model=TechReviewListDto)
def list_reviews(
    container: ContainerDep,
    project_id: str | None = Query(default=None),
) -> TechReviewListDto:
    items = container.list_tech_reviews.execute(ListTechReviewsQuery(project_id=project_id))
    return TechReviewListDto(
        items=[_present(container, item) for item in items]
    )


@router.post(
    "/api/tech/reviews",
    response_model=TechReviewDto,
    status_code=status.HTTP_201_CREATED,
)
def create_review(body: CreateTechReviewBody, container: ContainerDep) -> TechReviewDto:
    review = container.create_tech_review.execute(
        CreateTechReviewCommand(
            project_id=body.project_id,
            request_text=body.request_text,
            idempotency_key=body.idempotency_key,
            execution_mode=ExecutionMode(body.execution_mode),
        )
    )
    return _present(container, review)


@router.get("/api/tech/reviews/{review_id}", response_model=TechReviewDto)
def get_review(review_id: str, container: ContainerDep) -> TechReviewDto:
    review = container.get_tech_review.execute(GetTechReviewQuery(review_id=review_id))
    return _present(container, review)


@router.post("/api/tech/reviews/{review_id}/scenario", response_model=TechReviewDto)
def select_scenario(
    review_id: str,
    body: SelectScenarioBody,
    container: ContainerDep,
) -> TechReviewDto:
    review = container.select_tech_scenario.execute(
        SelectScenarioCommand(review_id=review_id, scenario_id=body.scenario_id)
    )
    return _present(container, review)


@router.post("/api/tech/reviews/{review_id}/run", response_model=TechReviewDto)
def run_pipeline(
    review_id: str,
    body: RunTechPipelineBody,
    container: ContainerDep,
) -> TechReviewDto:
    review = container.get_tech_review.execute(GetTechReviewQuery(review_id=review_id))
    if review.execution_mode == ExecutionMode.REAL:
        started = container.start_real_tech_review.execute(
            StartRealTechReviewCommand(
                review_id=review_id,
                idempotency_key=body.idempotency_key,
            )
        )
        return _present(container, started)
    ran = container.run_tech_pipeline.execute(
        RunTechPipelineCommand(
            review_id=review_id,
            idempotency_key=body.idempotency_key,
        )
    )
    return _present(container, ran)


@router.post("/api/tech/reviews/{review_id}/decision", response_model=TechReviewDto)
def decide_review(
    review_id: str,
    body: DecideTechReviewBody,
    container: ContainerDep,
) -> TechReviewDto:
    review = container.decide_tech_review.execute(
        DecideTechReviewCommand(
            review_id=review_id,
            proposal_id=body.proposal_id,
            proposal_version=body.proposal_version,
            rationale=body.rationale,
            idempotency_key=body.idempotency_key,
        )
    )
    return _present(container, review)


def _present(container: ContainerDep, review: TechReview) -> TechReviewDto:
    steps = container.step_store.list_steps(review.id)
    usage = container.budget_ledger.list_usage(review.id)
    reservation = container.budget_ledger.reservation_for(review.id)
    return review_to_dto(
        review,
        container.scenario_catalog,
        steps=steps,
        usage=usage,
        reservation=reservation,
    )
