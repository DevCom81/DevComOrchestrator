from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.domain.errors import MissionNotFoundError
from devcom.modules.missions.domain.mission import Mission
from devcom.modules.missions.ports.mission_repository import MissionRepository


@dataclass(frozen=True, slots=True)
class GetMissionQuery:
    mission_id: str


class GetMission:
    def __init__(self, repository: MissionRepository) -> None:
        self._repository = repository

    def execute(self, query: GetMissionQuery) -> Mission:
        mission = self._repository.get_by_id(query.mission_id)
        if mission is None:
            raise MissionNotFoundError(f"mission {query.mission_id} not found")
        return mission
