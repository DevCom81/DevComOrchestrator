from __future__ import annotations

from fastapi import APIRouter, Query, status

from devcom.entrypoints.http.deps import ContainerDep
from devcom.entrypoints.http.mission_presenter import mission_to_dto
from devcom.entrypoints.http.schemas.mission_schemas import (
    AnswerClarificationBody,
    CreateMissionBody,
    DemoExampleDto,
    DemoExampleListDto,
    MissionDto,
    MissionListDto,
)
from devcom.modules.missions.application.answer_clarification import (
    AnswerClarificationCommand,
)
from devcom.modules.missions.application.create_mission import CreateMissionCommand
from devcom.modules.missions.application.get_mission import GetMissionQuery
from devcom.modules.missions.application.list_missions import ListMissionsQuery

router = APIRouter(tags=["missions"])

DEMO_EXAMPLES = (
    DemoExampleDto(
        id="mail",
        label="Classer des mails",
        request_text="Classer ces mails",
    ),
    DemoExampleDto(
        id="sqlite",
        label="Persistance SQLite",
        request_text="Concevoir la persistance SQLite",
    ),
    DemoExampleDto(
        id="mixed",
        label="Mixte commercial + technique",
        request_text="Qualifier un prospect commercial et évaluer l'API technique",
    ),
    DemoExampleDto(
        id="external",
        label="Envoi mail (EXTERNAL)",
        request_text="Envoyer ce mail au client",
    ),
    DemoExampleDto(
        id="unknown",
        label="Demande non reconnue",
        request_text="Optimiser la stratégie globale de l'univers",
    ),
)


@router.get("/api/missions/demo-examples", response_model=DemoExampleListDto)
def demo_examples(container: ContainerDep) -> DemoExampleListDto:
    return DemoExampleListDto(
        items=list(DEMO_EXAMPLES),
        disclaimer=container.demo_dispatcher.meta.disclaimer,
    )


@router.get("/api/missions", response_model=MissionListDto)
def list_missions(
    container: ContainerDep,
    project_id: str | None = Query(default=None),
) -> MissionListDto:
    items = container.list_missions.execute(ListMissionsQuery(project_id=project_id))
    return MissionListDto(items=[mission_to_dto(item) for item in items])


@router.post(
    "/api/missions",
    response_model=MissionDto,
    status_code=status.HTTP_201_CREATED,
)
def create_mission(body: CreateMissionBody, container: ContainerDep) -> MissionDto:
    mission = container.create_mission.execute(
        CreateMissionCommand(project_id=body.project_id, request_text=body.request_text)
    )
    return mission_to_dto(mission)


@router.get("/api/missions/{mission_id}", response_model=MissionDto)
def get_mission(mission_id: str, container: ContainerDep) -> MissionDto:
    mission = container.get_mission.execute(GetMissionQuery(mission_id=mission_id))
    return mission_to_dto(mission)


@router.post("/api/missions/{mission_id}/clarifications", response_model=MissionDto)
def answer_clarification(
    mission_id: str,
    body: AnswerClarificationBody,
    container: ContainerDep,
) -> MissionDto:
    mission = container.answer_clarification.execute(
        AnswerClarificationCommand(
            mission_id=mission_id,
            clarification_token=body.clarification_token,
            answers=body.answers,
        )
    )
    return mission_to_dto(mission)
