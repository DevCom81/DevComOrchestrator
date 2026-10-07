from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.application.orchestrator import MissionOrchestrator
from devcom.modules.missions.domain.errors import ProjectMissingError
from devcom.modules.missions.domain.mission import Mission
from devcom.modules.missions.ports.mission_repository import MissionRepository
from devcom.modules.missions.ports.project_existence import ProjectExistencePort
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class CreateMissionCommand:
    project_id: str
    request_text: str


class CreateMission:
    def __init__(
        self,
        repository: MissionRepository,
        projects: ProjectExistencePort,
        orchestrator: MissionOrchestrator,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._projects = projects
        self._orchestrator = orchestrator
        self._clock = clock

    def execute(self, command: CreateMissionCommand) -> Mission:
        if not self._projects.exists(command.project_id):
            raise ProjectMissingError(f"project {command.project_id} not found")
        mission = Mission.create(command.project_id, command.request_text, self._clock.now())
        self._orchestrator.route_text(mission, mission.request_text, self._clock.now())
        self._repository.save_atomic(mission)
        return mission
