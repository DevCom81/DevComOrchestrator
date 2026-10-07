"""Code context roots, previews and immutable snapshots.

Revision ID: 0005_code_context
Revises: 0004_billing_real_pipeline
Create Date: 2026-10-07

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_code_context"
down_revision: Union[str, None] = "0004_billing_real_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_source_roots",
        sa.Column("project_id", sa.String(length=36), primary_key=True),
        sa.Column("absolute_path", sa.Text(), nullable=False),
        sa.Column("exclusions_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("attached_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "code_previews",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exclusions_json", sa.Text(), nullable=False),
        sa.Column("token_upper_bound", sa.Integer(), nullable=False),
        sa.Column("token_indicative", sa.Integer(), nullable=False),
        sa.Column("token_method_blocking", sa.String(length=64), nullable=False),
        sa.Column("token_method_indicative", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ready"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_code_previews_project_id", "code_previews", ["project_id"])
    op.create_table(
        "code_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("preview_id", sa.String(length=36), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exclusions_json", sa.Text(), nullable=False),
        sa.Column("git_commit", sa.String(length=64), nullable=True),
        sa.Column("git_dirty", sa.Integer(), nullable=True),
        sa.Column("git_note", sa.Text(), nullable=False),
        sa.Column("token_upper_bound", sa.Integer(), nullable=False),
        sa.Column("token_method_blocking", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="complete"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_code_snapshots_project_id", "code_snapshots", ["project_id"])
    with op.batch_alter_table("tech_reviews") as batch:
        batch.add_column(sa.Column("code_snapshot_id", sa.String(length=36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tech_reviews") as batch:
        batch.drop_column("code_snapshot_id")
    op.drop_index("ix_code_snapshots_project_id", table_name="code_snapshots")
    op.drop_table("code_snapshots")
    op.drop_index("ix_code_previews_project_id", table_name="code_previews")
    op.drop_table("code_previews")
    op.drop_table("project_source_roots")
