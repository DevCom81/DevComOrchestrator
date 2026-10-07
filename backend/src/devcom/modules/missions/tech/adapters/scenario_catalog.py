from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ScenarioMeta:
    id: str
    file: str
    label: str
    match_phrases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScenarioCatalog:
    version: int
    mode: str
    disclaimer: str
    scenarios: tuple[ScenarioMeta, ...]
    root: Path

    def match(self, request_text: str) -> ScenarioMeta | None:
        normalized = re.sub(r"\s+", " ", request_text.casefold()).strip()
        hits = [
            meta
            for meta in self.scenarios
            if any(phrase.casefold() in normalized for phrase in meta.match_phrases)
        ]
        if len(hits) == 1:
            return hits[0]
        return None

    def get(self, scenario_id: str) -> ScenarioMeta:
        for meta in self.scenarios:
            if meta.id == scenario_id:
                return meta
        raise KeyError(scenario_id)

    def load_payload(self, scenario_id: str) -> dict[str, Any]:
        meta = self.get(scenario_id)
        path = self.root / meta.file
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError(f"scenario `{scenario_id}` root must be an object")
        return payload

    def list_public(self) -> list[ScenarioMeta]:
        return list(self.scenarios)


def load_scenario_catalog(index_path: Path) -> ScenarioCatalog:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    root = index_path.parent
    scenarios = tuple(
        ScenarioMeta(
            id=item["id"],
            file=item["file"],
            label=item["label"],
            match_phrases=tuple(item.get("match_phrases", [])),
        )
        for item in payload["scenarios"]
    )
    return ScenarioCatalog(
        version=int(payload["version"]),
        mode=payload["mode"],
        disclaimer=payload["disclaimer"],
        scenarios=scenarios,
        root=root,
    )
