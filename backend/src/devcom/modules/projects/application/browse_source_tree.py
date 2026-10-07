from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.projects.adapters.safe_browser import browse_or_raise_empty_cursor, browse_tree
from devcom.modules.projects.adapters.sqlalchemy_code_context import SqlCodeContextStore
from devcom.modules.projects.application.code_context_support import (
    ensure_project,
    load_bounds,
    policy_for,
    resolve_root_path,
)


@dataclass(frozen=True, slots=True)
class BrowseSourceTreeQuery:
    project_id: str
    cursor: str | None = None


class BrowseSourceTree:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        store: SqlCodeContextStore,
        *,
        bounds_path: Path,
        exclusions_path: Path,
        mode: str,
        demo_fixture: Path,
    ) -> None:
        self._sessions = sessions
        self._store = store
        self._bounds_path = bounds_path
        self._exclusions_path = exclusions_path
        self._mode = mode
        self._demo_fixture = demo_fixture

    def execute(self, query: BrowseSourceTreeQuery) -> dict[str, object]:
        ensure_project(self._sessions, query.project_id)
        browse_or_raise_empty_cursor(query.cursor)
        root, globs = resolve_root_path(
            store=self._store,
            project_id=query.project_id,
            demo_fixture=self._demo_fixture,
            mode=self._mode,
        )
        bounds = load_bounds(self._bounds_path)
        policy = policy_for(
            exclusions_path=self._exclusions_path, root=root, project_globs=globs
        )
        page = browse_tree(root=root, policy=policy, bounds=bounds, cursor=query.cursor)
        return {
            "project_id": query.project_id,
            "root_path": str(root),
            "entries": [
                {
                    "relative_path": item.relative_path,
                    "name": item.name,
                    "kind": item.kind,
                    "excluded": item.excluded,
                    "exclusion_reason": item.exclusion_reason,
                }
                for item in page.entries
            ],
            "cursor": page.cursor,
            "truncated": page.truncated,
            "limit_message": page.limit_message,
            "secret_scan_disclaimer": (
                "Exclusions do not guarantee absence of secrets; "
                "explicit preview and selection remain mandatory."
            ),
        }
