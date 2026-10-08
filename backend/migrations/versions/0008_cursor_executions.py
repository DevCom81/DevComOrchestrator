"""Cursor executions, integrations, return execution link.

Revision ID: 0008_cursor_executions
Revises: 0007_cursor_plans
Create Date: 2026-10-08

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_cursor_executions"
down_revision: Union[str, None] = "0007_cursor_plans"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    plan_cols = {col["name"] for col in inspector.get_columns("cursor_plans")}
    if "corrections_used" not in plan_cols:
        op.add_column(
            "cursor_plans",
            sa.Column(
                "corrections_used", sa.Integer(), nullable=False, server_default="0"
            ),
        )
    ret_cols = {col["name"] for col in inspector.get_columns("cursor_returns")}
    if "execution_id" not in ret_cols:
        op.add_column(
            "cursor_returns",
            sa.Column("execution_id", sa.String(length=36), nullable=True),
        )
    # SQLite: batch recreate — plain ALTER COLUMN is unsupported
    with op.batch_alter_table("cursor_returns") as batch:
        batch.alter_column(
            "export_id",
            existing_type=sa.String(length=36),
            nullable=True,
        )
    tables = set(sa.inspect(bind).get_table_names())
    if "cursor_executions" not in tables:
        _create_executions()
    if "cursor_integrations" not in tables:
        _create_integrations()
    if "cursor_execution_reservations" not in tables:
        _create_reservations()


def _create_executions() -> None:
    op.create_table(
        "cursor_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "plan_id",
            sa.String(36),
            sa.ForeignKey("cursor_plans.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("correction_index", sa.Integer(), nullable=False),
        sa.Column("parent_execution_id", sa.String(36), nullable=True),
        sa.Column("execute_payload_hash", sa.String(64), nullable=False),
        sa.Column("execute_payload_json", sa.Text(), nullable=False),
        sa.Column("approval_id", sa.String(36), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("source_root", sa.Text(), nullable=False),
        sa.Column("git_base_commit", sa.String(64), nullable=False),
        sa.Column("model_id", sa.String(128), nullable=False),
        sa.Column("model_fast", sa.String(16), nullable=False),
        sa.Column("sandbox_policy_version", sa.String(64), nullable=False),
        sa.Column("reserved_eur_micros", sa.Integer(), nullable=False),
        sa.Column("worktree_path", sa.Text(), nullable=True),
        sa.Column("agent_id", sa.String(128), nullable=True),
        sa.Column("run_id", sa.String(128), nullable=True),
        sa.Column("cancel_requested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("writes_stable", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("capture_manifest_sha", sa.String(64), nullable=True),
        sa.Column("capture_incomplete", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("return_id", sa.String(36), nullable=True),
        sa.Column("usage_json", sa.Text(), nullable=True),
        sa.Column("billed_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def _create_integrations() -> None:
    op.create_table(
        "cursor_integrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "execution_id",
            sa.String(36),
            sa.ForeignKey("cursor_executions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("approval_id", sa.String(36), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("branch_name", sa.String(256), nullable=False),
        sa.Column("commit_sha", sa.String(64), nullable=True),
        sa.Column("worktree_path", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("merge_hint", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def _create_reservations() -> None:
    op.create_table(
        "cursor_execution_reservations",
        sa.Column("execution_id", sa.String(36), primary_key=True),
        sa.Column("month_id", sa.String(7), nullable=False),
        sa.Column("reserved_eur_micros", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("cursor_execution_reservations")
    op.drop_table("cursor_integrations")
    op.drop_table("cursor_executions")
    op.drop_column("cursor_returns", "execution_id")
    op.drop_column("cursor_plans", "corrections_used")
