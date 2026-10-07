from __future__ import annotations

from devcom.entrypoints.http.schemas.mission_schemas import (
    AuthorizationBlockDto,
    ClarificationChoiceDto,
    ClarificationQuestionDto,
    MissionDto,
    RoutingDto,
    TaskAssignmentDto,
)
from devcom.modules.missions.domain.mission import Mission


def mission_to_dto(mission: Mission) -> MissionDto:
    return MissionDto(
        id=mission.id,
        project_id=mission.project_id,
        request_text=mission.request_text,
        status=mission.status.value,
        created_at=mission.created_at,
        updated_at=mission.updated_at,
        routing=_routing_dto(mission),
        tasks=_task_dtos(mission),
        clarification_token=mission.clarification_token,
        clarification_questions=_question_dtos(mission),
        authorization_block=_block_dto(mission),
    )


def _routing_dto(mission: Mission) -> RoutingDto | None:
    routing = mission.routing
    if routing is None:
        return None
    return RoutingDto(
        mode=routing.mode,
        disclaimer=routing.disclaimer,
        rule_ids=list(routing.rule_ids),
        rationale=routing.rationale,
        capability_registry_version=routing.capability_registry_version,
        permission_policy_version=routing.permission_policy_version,
        dispatch_rules_version=routing.dispatch_rules_version,
    )


def _task_dtos(mission: Mission) -> list[TaskAssignmentDto]:
    return [
        TaskAssignmentDto(
            id=task.id,
            capability_id=task.capability_id,
            agent_id=task.agent_id,
            status=task.status.value,
            rationale=task.rationale,
        )
        for task in mission.tasks
    ]


def _question_dtos(mission: Mission) -> list[ClarificationQuestionDto]:
    return [
        ClarificationQuestionDto(
            id=question.id,
            prompt=question.prompt,
            choices=[
                ClarificationChoiceDto(
                    id=choice.id,
                    label=choice.label,
                    maps_to_rule=choice.maps_to_rule,
                )
                for choice in question.choices
            ],
        )
        for question in mission.clarification_questions
    ]


def _block_dto(mission: Mission) -> AuthorizationBlockDto | None:
    block = mission.authorization_block
    if block is None:
        return None
    return AuthorizationBlockDto(
        action_id=block.action_id,
        message=block.message,
        rationale=block.rationale,
    )
