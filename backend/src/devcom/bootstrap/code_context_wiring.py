from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from devcom.bootstrap.settings import Settings
from devcom.modules.missions.tech.adapters.code_snapshot_adapter import (
    ProjectCodeSnapshotAdapter,
)
from devcom.modules.projects.adapters.artifact_store import ArtifactStore
from devcom.modules.projects.adapters.sqlalchemy_code_context import SqlCodeContextStore
from devcom.modules.projects.application.attach_source_root import AttachSourceRoot
from devcom.modules.projects.application.browse_source_tree import BrowseSourceTree
from devcom.modules.projects.application.create_code_preview import CreateCodePreview
from devcom.modules.projects.application.detach_source_root import DetachSourceRoot
from devcom.modules.projects.application.freeze_code_snapshot import (
    FreezeCodeSnapshot,
    GetCodeSnapshot,
)
from devcom.modules.projects.application.get_source_root import GetSourceRoot
from devcom.shared.time import Clock


@dataclass(slots=True)
class CodeContextServices:
    store: SqlCodeContextStore
    artifacts: ArtifactStore
    attach_source_root: AttachSourceRoot
    detach_source_root: DetachSourceRoot
    get_source_root: GetSourceRoot
    browse_source_tree: BrowseSourceTree
    create_code_preview: CreateCodePreview
    freeze_code_snapshot: FreezeCodeSnapshot
    get_code_snapshot: GetCodeSnapshot
    code_snapshot_port: ProjectCodeSnapshotAdapter


def build_code_context_services(
    settings: Settings,
    sessions: sessionmaker[Session],
    clock: Clock,
) -> CodeContextServices:
    store = SqlCodeContextStore(sessions)
    artifacts = ArtifactStore(settings.data_dir)
    mode = settings.mode
    demo_fixture: Path = settings.demo_code_fixture
    return CodeContextServices(
        store=store,
        artifacts=artifacts,
        attach_source_root=AttachSourceRoot(
            sessions, store, clock, mode=mode, demo_fixture=demo_fixture
        ),
        detach_source_root=DetachSourceRoot(sessions, store),
        get_source_root=GetSourceRoot(
            sessions, store, mode=mode, demo_fixture=demo_fixture
        ),
        browse_source_tree=BrowseSourceTree(
            sessions,
            store,
            bounds_path=settings.filesystem_bounds_path,
            exclusions_path=settings.filesystem_exclusions_path,
            mode=mode,
            demo_fixture=demo_fixture,
        ),
        create_code_preview=CreateCodePreview(
            sessions,
            store,
            artifacts,
            clock,
            bounds_path=settings.filesystem_bounds_path,
            exclusions_path=settings.filesystem_exclusions_path,
            mode=mode,
            demo_fixture=demo_fixture,
        ),
        freeze_code_snapshot=FreezeCodeSnapshot(
            sessions,
            store,
            artifacts,
            clock,
            mode=mode,
            demo_fixture=demo_fixture,
        ),
        get_code_snapshot=GetCodeSnapshot(store, artifacts),
        code_snapshot_port=ProjectCodeSnapshotAdapter(store, artifacts),
    )
