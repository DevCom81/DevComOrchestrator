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
    export_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cursor_exports.id", ondelete="RESTRICT"), nullable=False, index=True
    )
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
