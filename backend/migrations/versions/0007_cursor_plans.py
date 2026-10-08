"""Cursor plans, approvals, exports and returns.

Revision ID: 0007_cursor_plans
Revises: 0006_tech_events
Create Date: 2026-10-07

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_cursor_plans"
down_revision: Union[str, None] = "0006_tech_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("action_id", sa.String(length=128), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("resource_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("author", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True, unique=True),
    )
    op.create_table(
        "cursor_plans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("review_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("proposal_id", sa.String(length=64), nullable=False),
        sa.Column("proposal_version", sa.Integer(), nullable=False),
        sa.Column("adr_id", sa.String(length=36), nullable=False),
        sa.Column("code_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("objectif", sa.Text(), nullable=False),
        sa.Column("perimetre", sa.Text(), nullable=False),
        sa.Column("exclusions", sa.Text(), nullable=False),
        sa.Column("contraintes_architecture", sa.Text(), nullable=False),
        sa.Column("criteres_acceptation", sa.Text(), nullable=False),
        sa.Column("validations_attendues", sa.Text(), nullable=False),
        sa.Column("markdown_utf8", sa.LargeBinary(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("canon_version", sa.String(length=64), nullable=False),
        sa.Column("active_approval_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["tech_reviews.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
    )
    op.create_table(
        "cursor_exports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("plan_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("approval_id", sa.String(length=36), nullable=False),
        sa.Column("markdown_utf8", sa.LargeBinary(), nullable=False),
        sa.Column("manifest_json", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["cursor_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approval_id"], ["approval_requests.id"], ondelete="RESTRICT"),
    )
    op.create_table(
        "cursor_returns",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("plan_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("export_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("project_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("report_sha256", sa.String(length=64), nullable=False),
        sa.Column("diff_sha256", sa.String(length=64), nullable=False),
        sa.Column("report_bytes", sa.Integer(), nullable=False),
        sa.Column("diff_bytes", sa.Integer(), nullable=False),
        sa.Column("declared_base", sa.Text(), nullable=True),
        sa.Column("declared_commit", sa.String(length=128), nullable=True),
        sa.Column("verification_status", sa.String(length=64), nullable=False),
        sa.Column("verification_notes", sa.Text(), nullable=False),
        sa.Column("artifact_dir", sa.String(length=512), nullable=False),
        sa.Column("linked_review_id", sa.String(length=36), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["cursor_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["export_id"], ["cursor_exports.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
    )


def downgrade() -> None:
    op.drop_table("cursor_returns")
    op.drop_table("cursor_exports")
    op.drop_table("cursor_plans")
    op.drop_table("approval_requests")
