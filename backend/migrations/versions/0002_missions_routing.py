"""Create missions and mission_tasks tables.

Revision ID: 0002_missions_routing
Revises: 0001_create_projects
Create Date: 2026-10-07

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_missions_routing"
down_revision: Union[str, None] = "0001_create_projects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "missions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("request_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("routing_mode", sa.String(length=64), nullable=True),
        sa.Column("routing_disclaimer", sa.Text(), nullable=True),
        sa.Column("routing_rule_ids", sa.Text(), nullable=True),
        sa.Column("routing_rationale", sa.Text(), nullable=True),
        sa.Column("capability_registry_version", sa.Integer(), nullable=True),
        sa.Column("permission_policy_version", sa.Integer(), nullable=True),
        sa.Column("dispatch_rules_version", sa.Integer(), nullable=True),
        sa.Column("clarification_token", sa.String(length=36), nullable=True),
        sa.Column("clarification_questions_json", sa.Text(), nullable=True),
        sa.Column("auth_block_action_id", sa.String(length=128), nullable=True),
        sa.Column("auth_block_message", sa.Text(), nullable=True),
        sa.Column("auth_block_rationale", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_missions_project_id", "missions", ["project_id"])
    op.create_index("ix_missions_status", "missions", ["status"])

    op.create_table(
        "mission_tasks",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("mission_id", sa.String(length=36), nullable=False),
        sa.Column("capability_id", sa.String(length=128), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_mission_tasks_mission_id", "mission_tasks", ["mission_id"])


def downgrade() -> None:
    op.drop_index("ix_mission_tasks_mission_id", table_name="mission_tasks")
    op.drop_table("mission_tasks")
    op.drop_index("ix_missions_status", table_name="missions")
    op.drop_index("ix_missions_project_id", table_name="missions")
    op.drop_table("missions")
