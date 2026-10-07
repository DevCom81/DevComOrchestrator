from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from devcom.shared.persistence import Base


class ProjectSourceRootRow(Base):
    __tablename__ = "project_source_roots"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    absolute_path: Mapped[str] = mapped_column(Text, nullable=False)
    exclusions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    attached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CodePreviewRow(Base):
    __tablename__ = "code_previews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exclusions_json: Mapped[str] = mapped_column(Text, nullable=False)
    token_upper_bound: Mapped[int] = mapped_column(Integer, nullable=False)
    token_indicative: Mapped[int] = mapped_column(Integer, nullable=False)
    token_method_blocking: Mapped[str] = mapped_column(String(64), nullable=False)
    token_method_indicative: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ready")


class CodeSnapshotRow(Base):
    __tablename__ = "code_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    preview_id: Mapped[str] = mapped_column(String(36), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exclusions_json: Mapped[str] = mapped_column(Text, nullable=False)
    git_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    git_dirty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    git_note: Mapped[str] = mapped_column(Text, nullable=False)
    token_upper_bound: Mapped[int] = mapped_column(Integer, nullable=False)
    token_method_blocking: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="complete")
