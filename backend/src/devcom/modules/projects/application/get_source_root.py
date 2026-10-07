from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.projects.adapters.sqlalchemy_code_context import SqlCodeContextStore
from devcom.modules.projects.application.code_context_support import ensure_project


@dataclass(frozen=True, slots=True)
class GetSourceRootQuery:
    project_id: str


class GetSourceRoot:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        store: SqlCodeContextStore,
        *,
        mode: str,
        demo_fixture: Path,
    ) -> None:
        self._sessions = sessions
        self._store = store
        self._mode = mode
        self._demo_fixture = demo_fixture

    def execute(self, query: GetSourceRootQuery) -> dict[str, object] | None:
        ensure_project(self._sessions, query.project_id)
        info = self._store.get_root(query.project_id)
        if self._mode == "demo":
            path = str(self._demo_fixture.resolve())
            exclusions: list[str] = []
            attached = None if info is None else info[2].isoformat()
            if info is not None:
                exclusions = list(info[1])
                path = info[0]
            return {
                "project_id": query.project_id,
                "absolute_path": path,
                "exclusions": exclusions,
                "attached_at": attached,
                "mode": "demo",
                "demo_fixture": True,
            }
        if info is None:
            return None
        return {
            "project_id": query.project_id,
            "absolute_path": info[0],
            "exclusions": list(info[1]),
            "attached_at": info[2].isoformat(),
            "mode": "real",
            "demo_fixture": False,
        }
