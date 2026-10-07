from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FileBlob:
    relative_path: str
    sha256: str
    byte_size: int
    content_text: str


@dataclass(frozen=True, slots=True)
class GitCaptureMeta:
    commit: str | None
    dirty: bool | None
    note: str


@dataclass(frozen=True, slots=True)
class CodePreview:
    id: str
    project_id: str
    fingerprint: str
    created_at: str
    expires_at: str
    files: tuple[FileBlob, ...]
    exclusions: tuple[str, ...]
    token_upper_bound: int
    token_indicative: int
    token_method_blocking: str
    token_method_indicative: str


@dataclass(frozen=True, slots=True)
class CodeSnapshot:
    id: str
    project_id: str
    preview_id: str
    fingerprint: str
    captured_at: str
    files: tuple[FileBlob, ...]
    exclusions: tuple[str, ...]
    git: GitCaptureMeta
    token_upper_bound: int
    token_method_blocking: str
    status: str
