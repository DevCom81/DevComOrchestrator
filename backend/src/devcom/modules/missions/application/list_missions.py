from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.domain.mission import Mission
from devcom.modules.missions.ports.mission_repository import MissionRepository


@dataclass(frozen=True, slots=True)
class ListMissionsQuery:
    project_id: str | None = None


class ListMissions:
    def __init__(self, repository: MissionRepository) -> None:
        self._repository = repository

    def execute(self, query: ListMissionsQuery) -> list[Mission]:
        return self._repository.list_for_project(query.project_id)
