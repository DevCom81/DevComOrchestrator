from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.projects.adapters.sqlalchemy_code_context import SqlCodeContextStore
from devcom.modules.projects.application.code_context_support import ensure_project


@dataclass(frozen=True, slots=True)
class DetachSourceRootCommand:
    project_id: str


class DetachSourceRoot:
    def __init__(self, sessions: sessionmaker[Session], store: SqlCodeContextStore) -> None:
        self._sessions = sessions
        self._store = store

    def execute(self, command: DetachSourceRootCommand) -> None:
        ensure_project(self._sessions, command.project_id)
        self._store.delete_root(command.project_id)
