from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from devcom.modules.missions.domain.errors import (
    MissionValidationError,
    StaleClarificationError,
)
from devcom.modules.missions.domain.mission_status import MissionStatus, TaskAssignmentStatus

REQUEST_MIN = 1
REQUEST_MAX = 2000
MAX_CLARIFICATION_QUESTIONS = 3


@dataclass(frozen=True, slots=True)
class ClarificationChoice:
    id: str
    label: str
    maps_to_rule: str


@dataclass(frozen=True, slots=True)
class ClarificationQuestion:
    id: str
    prompt: str
    choices: tuple[ClarificationChoice, ...]


@dataclass(frozen=True, slots=True)
class TaskAssignment:
    id: str
    capability_id: str
    agent_id: str
    status: TaskAssignmentStatus
    rationale: str


@dataclass(frozen=True, slots=True)
class AuthorizationBlock:
    action_id: str
    message: str
    rationale: str


@dataclass(frozen=True, slots=True)
class RoutingRecord:
    mode: str
    disclaimer: str
    rule_ids: tuple[str, ...]
    rationale: str
    capability_registry_version: int
    permission_policy_version: int
    dispatch_rules_version: int


@dataclass(slots=True)
class Mission:
    id: str
    project_id: str
    request_text: str
    status: MissionStatus
    created_at: datetime
    updated_at: datetime
    routing: RoutingRecord | None = None
    tasks: list[TaskAssignment] = field(default_factory=list)
    clarification_token: str | None = None
    clarification_questions: tuple[ClarificationQuestion, ...] = ()
    authorization_block: AuthorizationBlock | None = None

    @classmethod
    def create(cls, project_id: str, request_text: str, now: datetime) -> Mission:
        text = _parse_request(request_text)
        stamp = _utc(now)
        return cls(
            id=str(uuid4()),
            project_id=project_id,
            request_text=text,
            status=MissionStatus.DRAFT,
            created_at=stamp,
            updated_at=stamp,
        )

    def apply_routed(
        self,
        *,
        routing: RoutingRecord,
        tasks: list[TaskAssignment],
        now: datetime,
    ) -> None:
        self.routing = routing
        self.tasks = list(tasks)
        self.clarification_token = None
        self.clarification_questions = ()
        self.authorization_block = None
        self.status = MissionStatus.ROUTED
        self.updated_at = _utc(now)

    def apply_clarification(
        self,
        *,
        routing: RoutingRecord,
        questions: tuple[ClarificationQuestion, ...],
        now: datetime,
    ) -> None:
        if len(questions) == 0 or len(questions) > MAX_CLARIFICATION_QUESTIONS:
            raise MissionValidationError(
                f"clarification must contain 1 to {MAX_CLARIFICATION_QUESTIONS} questions"
            )
        self.routing = routing
        self.tasks = []
        self.authorization_block = None
        self.clarification_questions = questions
        self.clarification_token = str(uuid4())
        self.status = MissionStatus.AWAITING_CLARIFICATION
        self.updated_at = _utc(now)

    def apply_authorization_block(
        self,
        *,
        routing: RoutingRecord,
        block: AuthorizationBlock,
        now: datetime,
    ) -> None:
        self.routing = routing
        self.tasks = []
        self.clarification_token = None
        self.clarification_questions = ()
        self.authorization_block = block
        self.status = MissionStatus.BLOCKED_AUTHORIZATION
        self.updated_at = _utc(now)

    def require_clarification_token(self, token: str) -> None:
        if self.status != MissionStatus.AWAITING_CLARIFICATION:
            raise StaleClarificationError("mission is not awaiting clarification")
        if not self.clarification_token or self.clarification_token != token:
            raise StaleClarificationError("clarification token is obsolete")


def _parse_request(raw: str) -> str:
    text = raw.strip()
    if not (REQUEST_MIN <= len(text) <= REQUEST_MAX):
        raise MissionValidationError(
            f"request must be {REQUEST_MIN} to {REQUEST_MAX} characters after trim"
        )
    return text


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise MissionValidationError("timestamps must be timezone-aware UTC")
    return value.astimezone(UTC)
