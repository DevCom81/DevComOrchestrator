from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClarificationChoiceDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    maps_to_rule: str


class ClarificationQuestionDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    prompt: str
    choices: list[ClarificationChoiceDto]


class TaskAssignmentDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    capability_id: str
    agent_id: str
    status: str
    rationale: str


class RoutingDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    disclaimer: str
    rule_ids: list[str]
    rationale: str
    capability_registry_version: int
    permission_policy_version: int
    dispatch_rules_version: int


class AuthorizationBlockDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str
    message: str
    rationale: str


class MissionDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    project_id: str
    request_text: str
    status: str
    created_at: datetime
    updated_at: datetime
    routing: RoutingDto | None
    tasks: list[TaskAssignmentDto]
    clarification_token: str | None
    clarification_questions: list[ClarificationQuestionDto]
    authorization_block: AuthorizationBlockDto | None


class MissionListDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[MissionDto]


class CreateMissionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=36)
    request_text: str = Field(min_length=1, max_length=4000)


class AnswerClarificationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clarification_token: str = Field(min_length=1, max_length=36)
    answers: dict[str, str]


class DemoExampleDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    request_text: str


class DemoExampleListDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DemoExampleDto]
    disclaimer: str
