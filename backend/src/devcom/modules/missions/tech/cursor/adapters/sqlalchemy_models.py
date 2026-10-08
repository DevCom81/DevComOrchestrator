from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from devcom.shared.persistence import Base


class CursorPlanRow(Base):
    __tablename__ = "cursor_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    review_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tech_reviews.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    proposal_id: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_version: Mapped[int] = mapped_column(Integer, nullable=False)
    adr_id: Mapped[str] = mapped_column(String(36), nullable=False)
    code_snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False)
    objectif: Mapped[str] = mapped_column(Text, nullable=False)
    perimetre: Mapped[str] = mapped_column(Text, nullable=False)
    exclusions: Mapped[str] = mapped_column(Text, nullable=False)
    contraintes_architecture: Mapped[str] = mapped_column(Text, nullable=False)
    criteres_acceptation: Mapped[str] = mapped_column(Text, nullable=False)
    validations_attendues: Mapped[str] = mapped_column(Text, nullable=False)
    markdown_utf8: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    canon_version: Mapped[str] = mapped_column(String(64), nullable=False)
    active_approval_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    corrections_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CursorExportRow(Base):
    __tablename__ = "cursor_exports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cursor_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    approval_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("approval_requests.id", ondelete="RESTRICT"), nullable=False
    )
    markdown_utf8: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CursorReturnRow(Base):
    __tablename__ = "cursor_returns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cursor_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    export_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cursor_exports.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    execution_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    report_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    diff_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    report_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    diff_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    declared_base: Mapped[str | None] = mapped_column(Text, nullable=True)
    declared_commit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_notes: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_dir: Mapped[str] = mapped_column(String(512), nullable=False)
    linked_review_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CursorExecutionRow(Base):
    __tablename__ = "cursor_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cursor_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    correction_index: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_execution_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    execute_payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    execute_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    approval_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    source_root: Mapped[str] = mapped_column(Text, nullable=False)
    git_base_commit: Mapped[str] = mapped_column(String(64), nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    model_fast: Mapped[str] = mapped_column(String(16), nullable=False)
    sandbox_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    reserved_eur_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    worktree_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cancel_requested: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    writes_stable: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    capture_manifest_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capture_incomplete: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    return_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    usage_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    billed_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CursorIntegrationRow(Base):
    __tablename__ = "cursor_integrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cursor_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    approval_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    branch_name: Mapped[str] = mapped_column(String(256), nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    worktree_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    merge_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CursorExecutionReservationRow(Base):
    __tablename__ = "cursor_execution_reservations"

    execution_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    month_id: Mapped[str] = mapped_column(String(7), nullable=False)
    reserved_eur_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
