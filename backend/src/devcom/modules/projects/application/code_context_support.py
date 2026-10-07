from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.projects.adapters.exclusion_loader import build_policy, load_hard_exclusions
from devcom.modules.projects.adapters.sqlalchemy_code_context import SqlCodeContextStore
from devcom.modules.projects.adapters.sqlalchemy_models import ProjectRow
from devcom.modules.projects.domain.bounds import FilesystemBounds
from devcom.modules.projects.domain.errors import ProjectNotFoundError, SourceRootError
from devcom.modules.projects.domain.exclusion_policy import ExclusionPolicy


def load_bounds(path: Path) -> FilesystemBounds:
    return FilesystemBounds.from_dict(json.loads(path.read_text(encoding="utf-8")))


def ensure_project(sessions: sessionmaker[Session], project_id: str) -> None:
    with sessions() as session:
        if session.get(ProjectRow, project_id) is None:
            raise ProjectNotFoundError(f"project {project_id} not found")


def resolve_root_path(
    *,
    store: SqlCodeContextStore,
    project_id: str,
    demo_fixture: Path | None,
    mode: str,
) -> tuple[Path, tuple[str, ...]]:
    if mode == "demo":
        if demo_fixture is None or not demo_fixture.is_dir():
            raise SourceRootError("demo code fixture missing")
        root_info = store.get_root(project_id)
        globs = () if root_info is None else root_info[1]
        return demo_fixture, globs
    root_info = store.get_root(project_id)
    if root_info is None:
        raise SourceRootError("no source root attached")
    return Path(root_info[0]), root_info[1]


def policy_for(
    *,
    exclusions_path: Path,
    root: Path,
    project_globs: tuple[str, ...],
) -> ExclusionPolicy:
    contract = load_hard_exclusions(exclusions_path)
    return build_policy(
        contract=contract,
        project_globs=project_globs,
        root=root,
        apply_gitignore=True,
    )
