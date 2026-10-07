from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.tech.adapters.scenario_catalog import ScenarioCatalog, ScenarioMeta


@dataclass(frozen=True, slots=True)
class ScenarioListItem:
    id: str
    label: str


class ListTechScenarios:
    def __init__(self, catalog: ScenarioCatalog) -> None:
        self._catalog = catalog

    def execute(self) -> tuple[list[ScenarioListItem], str]:
        items = [
            ScenarioListItem(id=meta.id, label=meta.label)
            for meta in self._catalog.list_public()
        ]
        return items, self._catalog.disclaimer


def suggested_scenario_id(catalog: ScenarioCatalog, request_text: str) -> str | None:
    meta: ScenarioMeta | None = catalog.match(request_text)
    return None if meta is None else meta.id
