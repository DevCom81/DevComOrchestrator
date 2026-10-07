"""Create tech review tables.

Revision ID: 0003_tech_reviews
Revises: 0002_missions_routing
Create Date: 2026-10-07

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_tech_reviews"
down_revision: Union[str, None] = "0002_missions_routing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _create_tech_reviews()
    _create_decisions_and_adrs()
    _create_idempotency()


def _create_tech_reviews() -> None:
    op.create_table(
        "tech_reviews",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("request_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("unmatched_request", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scenario_id", sa.String(length=128), nullable=True),
        sa.Column("scenario_version", sa.Integer(), nullable=True),
        sa.Column("scenario_label_note", sa.Text(), nullable=True),
        sa.Column("snapshot_json", sa.Text(), nullable=True),
        sa.Column("analyses_json", sa.Text(), nullable=True),
        sa.Column("challenges_json", sa.Text(), nullable=True),
        sa.Column("synthesis_json", sa.Text(), nullable=True),
        sa.Column("proposals_json", sa.Text(), nullable=True),
        sa.Column("proposals_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("capability_registry_version", sa.Integer(), nullable=True),
        sa.Column("permission_policy_version", sa.Integer(), nullable=True),
        sa.Column("blocking_policy_version", sa.Integer(), nullable=True),
        sa.Column("create_idempotency_key", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("create_idempotency_key", name="uq_tech_reviews_create_key"),
    )
    op.create_index("ix_tech_reviews_project_id", "tech_reviews", ["project_id"])
    op.create_index("ix_tech_reviews_status", "tech_reviews", ["status"])


def _create_decisions_and_adrs() -> None:
    op.create_table(
        "tech_decisions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("review_id", sa.String(length=36), nullable=False),
        sa.Column("proposal_id", sa.String(length=64), nullable=False),
        sa.Column("proposal_version", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=128), nullable=False),
        sa.Column("decided_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["tech_reviews.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("review_id", name="uq_tech_decisions_review"),
    )
    op.create_table(
        "tech_adrs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("review_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("demo_warning", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["tech_reviews.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("review_id", name="uq_tech_adrs_review"),
    )


def _create_idempotency() -> None:
    op.create_table(
        "tech_idempotency",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=36), nullable=False),
        sa.UniqueConstraint("operation", "key", name="uq_tech_idempotency_op_key"),
    )


def downgrade() -> None:
    op.drop_table("tech_idempotency")
    op.drop_table("tech_adrs")
    op.drop_table("tech_decisions")
    op.drop_index("ix_tech_reviews_status", table_name="tech_reviews")
    op.drop_index("ix_tech_reviews_project_id", table_name="tech_reviews")
    op.drop_table("tech_reviews")
