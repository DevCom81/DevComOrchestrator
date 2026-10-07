from __future__ import annotations

from devcom.entrypoints.http.schemas.code_context_schemas import (
    CodeSourceFileDto,
    CodeSourcesDto,
)
from devcom.modules.missions.tech.application.code_sources import sources_payload
from devcom.modules.projects.domain.code_artifacts import CodeSnapshot


def code_sources_dto(snapshot: CodeSnapshot | None) -> CodeSourcesDto:
    payload = sources_payload(snapshot)
    files = [
        CodeSourceFileDto(
            relative_path=str(item["relative_path"]),
            sha256=str(item["sha256"]),
            byte_size=int(item["byte_size"]),
            evidence_ref=str(item["evidence_ref"]),
        )
        for item in payload.get("files", [])
    ]
    git = payload.get("git") or {}
    return CodeSourcesDto(
        has_code_sources=bool(payload["has_code_sources"]),
        notice=str(payload["notice"]),
        snapshot_id=None if snapshot is None else snapshot.id,
        fingerprint=None if snapshot is None else snapshot.fingerprint,
        captured_at=None if snapshot is None else snapshot.captured_at,
        git_commit=git.get("commit") if isinstance(git, dict) else None,
        git_dirty=git.get("dirty") if isinstance(git, dict) else None,
        git_note=git.get("note") if isinstance(git, dict) else None,
        files=files,
    )
