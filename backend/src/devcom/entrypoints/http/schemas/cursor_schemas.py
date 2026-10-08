from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CursorPlanDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    project_id: str
    review_id: str
    proposal_id: str
    proposal_version: int
    adr_id: str
    code_snapshot_id: str | None
    status: str
    plan_version: int
    objectif: str
    perimetre: str
    exclusions: str
    contraintes_architecture: str
    criteres_acceptation: str
    validations_attendues: str
    content_hash: str
    canon_version: str
    active_approval_id: str | None
    corrections_used: int
    preview_text: str
    created_at: datetime
    updated_at: datetime


class CursorPlanListDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CursorPlanDto]


class UpdateCursorPlanBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    objectif: str = Field(min_length=1, max_length=4000)
    perimetre: str = Field(min_length=1, max_length=4000)
    exclusions: str = Field(min_length=1, max_length=4000)
    contraintes_architecture: str = Field(min_length=1, max_length=4000)
    criteres_acceptation: str = Field(min_length=1, max_length=4000)
    validations_attendues: str = Field(min_length=1, max_length=4000)


class IdempotencyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=1, max_length=128)


class RequestGoBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=128)


class DecideGoBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grant: bool


class ApprovalDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    action_id: str
    target_id: str
    payload_hash: str
    resource_version: int
    status: str
    author: str
    created_at: datetime
    expires_at: datetime
    decided_at: datetime | None
    consumed_at: datetime | None


class CursorExportDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    plan_id: str
    plan_version: int
    content_hash: str
    approval_id: str
    manifest_json: str
    created_at: datetime
    download_markdown: str


class ImportReturnBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    export_id: str = Field(min_length=1, max_length=36)
    report_text: str = Field(min_length=1)
    diff_text: str = Field(min_length=1)
    declared_base: str | None = Field(default=None, max_length=2000)
    declared_commit: str | None = Field(default=None, max_length=128)


class CursorReturnDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    plan_id: str
    export_id: str | None
    execution_id: str | None = None
    project_id: str
    report_sha256: str
    diff_sha256: str
    report_bytes: int
    diff_bytes: int
    declared_base: str | None
    declared_commit: str | None
    verification_status: str
    verification_notes: str
    linked_review_id: str | None
    imported_at: datetime


class ReturnContextDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    return_id: str
    plan_id: str
    export_id: str | None
    execution_id: str | None = None
    export_content_hash: str
    export_plan_version: int
    code_snapshot_id: str | None
    report_sha256: str
    diff_sha256: str
    report_bytes: int
    diff_bytes: int
    verification_status: str
    verification_notes: str
    declared_base: str | None
    declared_commit: str | None
    report_text: str
    diff_text: str
    warning: str


class CreateReturnReviewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=1, max_length=128)
    execution_mode: str = Field(default="demo", pattern="^(demo|real)$")


class RequestExecuteGoBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=128)
    source_root: str = Field(min_length=1, max_length=4096)
    correction: bool = False
    prior_execution_id: str | None = None
    review_observations: str = Field(default="", max_length=8000)


class StartExecutionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str = Field(min_length=1, max_length=36)
    idempotency_key: str = Field(min_length=1, max_length=128)
    payload_json: str = Field(min_length=2)
    payload_hash: str = Field(min_length=64, max_length=64)


class ExecutePreviewDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: dict[str, object]
    payload_hash: str
    payload_json: str
    budget_layers: dict[str, object]
    approval: ApprovalDto


class CursorExecutionDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    plan_id: str
    project_id: str
    status: str
    correction_index: int
    content_hash: str
    git_base_commit: str
    model_id: str
    cancel_requested: bool
    writes_stable: bool
    capture_manifest_sha: str | None
    capture_incomplete: bool
    return_id: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class IntegratePreviewDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preview: dict[str, object]
    approval: ApprovalDto


class CursorIntegrationDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    execution_id: str
    status: str
    branch_name: str
    commit_sha: str | None
    worktree_path: str | None
    summary: str | None
    merge_hint: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ApplyIntegrateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str = Field(min_length=1, max_length=36)
    idempotency_key: str = Field(min_length=1, max_length=128)
