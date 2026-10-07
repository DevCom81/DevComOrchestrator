from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.projects.adapters.safe_path import assert_usable_root
from devcom.modules.projects.adapters.sqlalchemy_code_context import SqlCodeContextStore
from devcom.modules.projects.application.code_context_support import ensure_project
from devcom.modules.projects.domain.errors import SourceRootError
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class AttachSourceRootCommand:
    project_id: str
    absolute_path: str
    exclusions: tuple[str, ...] = ()


class AttachSourceRoot:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        store: SqlCodeContextStore,
        clock: Clock,
        *,
        mode: str,
        demo_fixture: Path,
    ) -> None:
        self._sessions = sessions
        self._store = store
        self._clock = clock
        self._mode = mode
        self._demo_fixture = demo_fixture

    def execute(self, command: AttachSourceRootCommand) -> dict[str, object]:
        ensure_project(self._sessions, command.project_id)
        if self._mode == "demo":
            path = assert_usable_root(self._demo_fixture.resolve())
            note = "demo mode — fixture root only"
        else:
            path = assert_usable_root(Path(command.absolute_path).expanduser())
            note = "real mode — local root attached"
            if not path.is_absolute():
                raise SourceRootError("absolute path required")
        now = self._clock.now()
        self._store.upsert_root(
            project_id=command.project_id,
            absolute_path=str(path),
            exclusions=command.exclusions,
            attached_at=now,
        )
        return {
            "project_id": command.project_id,
            "absolute_path": str(path),
            "exclusions": list(command.exclusions),
            "attached_at": now.isoformat(),
            "mode": self._mode,
            "demo_fixture": self._mode == "demo",
            "note": note,
        }
