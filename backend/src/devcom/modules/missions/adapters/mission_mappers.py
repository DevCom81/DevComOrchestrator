from __future__ import annotations

import json
from datetime import UTC, datetime

from devcom.modules.missions.adapters.sqlalchemy_models import MissionRow, MissionTaskRow
from devcom.modules.missions.domain.mission import (
    AuthorizationBlock,
    ClarificationChoice,
    ClarificationQuestion,
    Mission,
    RoutingRecord,
    TaskAssignment,
)
from devcom.modules.missions.domain.mission_status import MissionStatus, TaskAssignmentStatus


def mission_to_row(mission: Mission) -> MissionRow:
    routing = mission.routing
    block = mission.authorization_block
    return MissionRow(
        id=mission.id,
        project_id=mission.project_id,
        request_text=mission.request_text,
        status=mission.status.value,
        created_at=mission.created_at,
        updated_at=mission.updated_at,
        routing_mode=None if routing is None else routing.mode,
        routing_disclaimer=None if routing is None else routing.disclaimer,
        routing_rule_ids=None if routing is None else json.dumps(list(routing.rule_ids)),
        routing_rationale=None if routing is None else routing.rationale,
        capability_registry_version=(
            None if routing is None else routing.capability_registry_version
        ),
        permission_policy_version=(
            None if routing is None else routing.permission_policy_version
        ),
        dispatch_rules_version=None if routing is None else routing.dispatch_rules_version,
        clarification_token=mission.clarification_token,
        clarification_questions_json=_questions_to_json(mission.clarification_questions),
        auth_block_action_id=None if block is None else block.action_id,
        auth_block_message=None if block is None else block.message,
        auth_block_rationale=None if block is None else block.rationale,
    )


def task_to_row(task: TaskAssignment, mission_id: str) -> MissionTaskRow:
    return MissionTaskRow(
        id=task.id,
        mission_id=mission_id,
        capability_id=task.capability_id,
        agent_id=task.agent_id,
        status=task.status.value,
        rationale=task.rationale,
    )


def row_to_mission(row: MissionRow, task_rows: list[MissionTaskRow]) -> Mission:
    return Mission(
        id=row.id,
        project_id=row.project_id,
        request_text=row.request_text,
        status=MissionStatus(row.status),
        created_at=_utc(row.created_at),
        updated_at=_utc(row.updated_at),
        routing=_routing_from_row(row),
        tasks=[_task_from_row(item) for item in task_rows],
        clarification_token=row.clarification_token,
        clarification_questions=_questions_from_json(row.clarification_questions_json),
        authorization_block=_block_from_row(row),
    )


def _routing_from_row(row: MissionRow) -> RoutingRecord | None:
    if row.routing_mode is None:
        return None
    return RoutingRecord(
        mode=row.routing_mode,
        disclaimer=row.routing_disclaimer or "",
        rule_ids=tuple(json.loads(row.routing_rule_ids or "[]")),
        rationale=row.routing_rationale or "",
        capability_registry_version=int(row.capability_registry_version or 0),
        permission_policy_version=int(row.permission_policy_version or 0),
        dispatch_rules_version=int(row.dispatch_rules_version or 0),
    )


def _block_from_row(row: MissionRow) -> AuthorizationBlock | None:
    if row.auth_block_action_id is None:
        return None
    return AuthorizationBlock(
        action_id=row.auth_block_action_id,
        message=row.auth_block_message or "",
        rationale=row.auth_block_rationale or "",
    )


def _task_from_row(row: MissionTaskRow) -> TaskAssignment:
    return TaskAssignment(
        id=row.id,
        capability_id=row.capability_id,
        agent_id=row.agent_id,
        status=TaskAssignmentStatus(row.status),
        rationale=row.rationale,
    )


def _questions_to_json(questions: tuple[ClarificationQuestion, ...]) -> str | None:
    if not questions:
        return None
    payload = [
        {
            "id": question.id,
            "prompt": question.prompt,
            "choices": [
                {
                    "id": choice.id,
                    "label": choice.label,
                    "maps_to_rule": choice.maps_to_rule,
                }
                for choice in question.choices
            ],
        }
        for question in questions
    ]
    return json.dumps(payload)


def _questions_from_json(raw: str | None) -> tuple[ClarificationQuestion, ...]:
    if not raw:
        return ()
    payload = json.loads(raw)
    return tuple(
        ClarificationQuestion(
            id=item["id"],
            prompt=item["prompt"],
            choices=tuple(
                ClarificationChoice(
                    id=choice["id"],
                    label=choice["label"],
                    maps_to_rule=choice["maps_to_rule"],
                )
                for choice in item["choices"]
            ),
        )
        for item in payload
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
