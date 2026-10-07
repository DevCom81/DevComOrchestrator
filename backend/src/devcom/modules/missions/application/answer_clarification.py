from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.application.orchestrator import MissionOrchestrator
from devcom.modules.missions.domain.errors import (
    MissionNotFoundError,
    MissionValidationError,
)
from devcom.modules.missions.domain.mission import Mission
from devcom.modules.missions.ports.mission_repository import MissionRepository
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class AnswerClarificationCommand:
    mission_id: str
    clarification_token: str
    answers: dict[str, str]


class AnswerClarification:
    def __init__(
        self,
        repository: MissionRepository,
        orchestrator: MissionOrchestrator,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._orchestrator = orchestrator
        self._clock = clock

    def execute(self, command: AnswerClarificationCommand) -> Mission:
        mission = self._repository.get_by_id(command.mission_id)
        if mission is None:
            raise MissionNotFoundError(f"mission {command.mission_id} not found")
        mission.require_clarification_token(command.clarification_token)
        rule_id = self._resolve_rule(mission, command.answers)
        self._orchestrator.route_from_rule(mission, rule_id, self._clock.now())
        self._repository.save_atomic(mission)
        return mission

    def _resolve_rule(self, mission: Mission, answers: dict[str, str]) -> str:
        if not mission.clarification_questions:
            raise MissionValidationError("no clarification questions available")
        question = mission.clarification_questions[0]
        choice_id = answers.get(question.id)
        if choice_id is None:
            raise MissionValidationError(f"missing answer for `{question.id}`")
        for choice in question.choices:
            if choice.id == choice_id:
                return choice.maps_to_rule
        raise MissionValidationError(f"unknown choice `{choice_id}`")
