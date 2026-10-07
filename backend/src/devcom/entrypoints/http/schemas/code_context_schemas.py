from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AttachSourceRootBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    absolute_path: str = Field(min_length=1, max_length=4096)
    exclusions: list[str] = Field(default_factory=list, max_length=50)


class SourceRootDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str
    absolute_path: str
    exclusions: list[str]
    attached_at: str | None = None
    mode: str
    demo_fixture: bool
    note: str | None = None


class TreeEntryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relative_path: str
    name: str
    kind: str
    excluded: bool
    exclusion_reason: str | None


class SourceTreeDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str
    root_path: str
    entries: list[TreeEntryDto]
    cursor: str | None
    truncated: bool
    limit_message: str | None
    secret_scan_disclaimer: str


class PreviewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relative_paths: list[str] = Field(min_length=1, max_length=40)


class PreviewFileDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relative_path: str
    sha256: str
    byte_size: int
    content: str
    evidence_ref: str


class CodePreviewDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preview_id: str
    project_id: str
    fingerprint: str
    created_at: str
    expires_at: str
    files: list[PreviewFileDto]
    exclusions: list[str]
    token_upper_bound: int
    token_indicative: int
    token_method_blocking: str
    token_method_indicative: str
    reserves_budget: bool = False
    provider_calls: int = 0


class FreezeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preview_id: str = Field(min_length=1, max_length=36)


class CodeSnapshotDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    project_id: str
    preview_id: str
    fingerprint: str
    captured_at: str
    files: list[PreviewFileDto]
    exclusions: list[str]
    git_commit: str | None
    git_dirty: bool | None
    git_note: str
    token_upper_bound: int
    token_method_blocking: str
    status: str


class CodeSourceFileDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relative_path: str
    sha256: str
    byte_size: int
    evidence_ref: str


class CodeSourcesDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    has_code_sources: bool
    notice: str
    snapshot_id: str | None = None
    fingerprint: str | None = None
    captured_at: str | None = None
    git_commit: str | None = None
    git_dirty: bool | None = None
    git_note: str | None = None
    files: list[CodeSourceFileDto] = Field(default_factory=list)
