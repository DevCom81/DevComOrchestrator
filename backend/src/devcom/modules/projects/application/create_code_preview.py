from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.projects.adapters.artifact_store import ArtifactStore
from devcom.modules.projects.adapters.safe_browser import require_relative_under_listing
from devcom.modules.projects.adapters.safe_reader import read_text_file
from devcom.modules.projects.adapters.sqlalchemy_code_context import SqlCodeContextStore
from devcom.modules.projects.adapters.token_counter import estimate_blob_tokens
from devcom.modules.projects.application.code_context_support import (
    ensure_project,
    load_bounds,
    policy_for,
    resolve_root_path,
)
from devcom.modules.projects.domain.bounds import FilesystemBounds
from devcom.modules.projects.domain.code_artifacts import CodePreview, FileBlob
from devcom.modules.projects.domain.errors import BoundsExceededError
from devcom.modules.projects.domain.exclusion_policy import ExclusionPolicy
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class CreateCodePreviewCommand:
    project_id: str
    relative_paths: tuple[str, ...]


class CreateCodePreview:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        store: SqlCodeContextStore,
        artifacts: ArtifactStore,
        clock: Clock,
        *,
        bounds_path: Path,
        exclusions_path: Path,
        mode: str,
        demo_fixture: Path,
    ) -> None:
        self._sessions = sessions
        self._store = store
        self._artifacts = artifacts
        self._clock = clock
        self._bounds_path = bounds_path
        self._exclusions_path = exclusions_path
        self._mode = mode
        self._demo_fixture = demo_fixture

    def execute(self, command: CreateCodePreviewCommand) -> CodePreview:
        ensure_project(self._sessions, command.project_id)
        bounds = load_bounds(self._bounds_path)
        if len(command.relative_paths) > bounds.max_files_per_snapshot:
            raise BoundsExceededError("too many files selected")
        root, globs = resolve_root_path(
            store=self._store,
            project_id=command.project_id,
            demo_fixture=self._demo_fixture,
            mode=self._mode,
        )
        policy = policy_for(
            exclusions_path=self._exclusions_path, root=root, project_globs=globs
        )
        files, exclusions = self._read_all(root, policy, bounds, command.relative_paths)
        total_bytes = sum(item.byte_size for item in files)
        if total_bytes > bounds.max_bytes_per_snapshot:
            raise BoundsExceededError("snapshot byte budget exceeded")
        tokens = estimate_blob_tokens(tuple(item.content_text for item in files))
        if tokens.upper_bound > bounds.max_estimated_tokens_per_snapshot:
            raise BoundsExceededError("token upper bound exceeds snapshot cap")
        now = self._clock.now()
        preview_id = str(uuid4())
        fingerprint = self._artifacts.write_files_atomic(
            self._artifacts.preview_dir(preview_id), files
        )
        preview = CodePreview(
            id=preview_id,
            project_id=command.project_id,
            fingerprint=fingerprint,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=bounds.preview_ttl_seconds)).isoformat(),
            files=files,
            exclusions=tuple(exclusions),
            token_upper_bound=tokens.upper_bound,
            token_indicative=tokens.indicative,
            token_method_blocking=tokens.blocking_method,
            token_method_indicative=tokens.indicative_method,
        )
        self._store.save_preview_meta(preview)
        return preview

    def _read_all(
        self,
        root: Path,
        policy: ExclusionPolicy,
        bounds: FilesystemBounds,
        paths: tuple[str, ...],
    ) -> tuple[tuple[FileBlob, ...], list[str]]:
        files: list[FileBlob] = []
        exclusions: list[str] = []
        seen: set[str] = set()
        for raw in paths:
            relative = require_relative_under_listing(raw)
            if relative in seen:
                continue
            seen.add(relative)
            result = read_text_file(
                root=root, relative=relative, policy=policy, bounds=bounds
            )
            files.append(
                FileBlob(
                    relative_path=result.relative_path,
                    sha256=result.sha256,
                    byte_size=result.byte_size,
                    content_text=result.content_text,
                )
            )
        if not files:
            raise BoundsExceededError("no files readable for preview")
        return tuple(files), exclusions
