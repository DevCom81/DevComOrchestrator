"""Billing ledger and real TECH pipeline steps.

Revision ID: 0004_billing_real_pipeline
Revises: 0003_tech_reviews
Create Date: 2026-10-07

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_billing_real_pipeline"
down_revision: Union[str, None] = "0003_tech_reviews"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _alter_tech_reviews()
    _create_steps()
    _create_billing()


def _alter_tech_reviews() -> None:
    op.add_column(
        "tech_reviews",
        sa.Column("execution_mode", sa.String(length=16), nullable=False, server_default="demo"),
    )
    op.add_column("tech_reviews", sa.Column("plan_json", sa.Text(), nullable=True))
    op.add_column("tech_reviews", sa.Column("envelope_usd_micros", sa.Integer(), nullable=True))
    op.add_column("tech_reviews", sa.Column("envelope_eur_micros", sa.Integer(), nullable=True))
    op.add_column("tech_reviews", sa.Column("failure_message", sa.Text(), nullable=True))
    op.add_column("tech_reviews", sa.Column("frozen_models_json", sa.Text(), nullable=True))


def _create_steps() -> None:
    op.create_table(
        "tech_pipeline_steps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("review_id", sa.String(length=36), nullable=False),
        sa.Column("step_key", sa.String(length=128), nullable=False),
        sa.Column("phase", sa.String(length=32), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("optional", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("cost_status", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["review_id"], ["tech_reviews.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("review_id", "step_key", name="uq_tech_pipeline_steps"),
    )
    op.create_index("ix_tech_pipeline_steps_review_id", "tech_pipeline_steps", ["review_id"])


def _create_billing() -> None:
    op.create_table(
        "budget_periods",
        sa.Column("month_id", sa.String(length=7), primary_key=True),
        sa.Column("cap_eur_micros", sa.Integer(), nullable=False),
        sa.Column("confirmed_eur_micros", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_eur_micros", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uncertain_eur_micros", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "budget_reservations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("review_id", sa.String(length=36), nullable=False),
        sa.Column("month_id", sa.String(length=7), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("envelope_usd_micros", sa.Integer(), nullable=False),
        sa.Column("envelope_eur_micros", sa.Integer(), nullable=False),
        sa.Column("confirmed_usd_micros", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confirmed_eur_micros", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fx_rate", sa.String(length=32), nullable=False),
        sa.Column("fx_rate_date", sa.String(length=32), nullable=False),
        sa.Column("fx_margin_ratio", sa.String(length=32), nullable=False),
        sa.Column("rates_verified_at", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("review_id", name="uq_budget_reservations_review"),
    )
    op.create_index("ix_budget_reservations_review_id", "budget_reservations", ["review_id"])
    op.create_table(
        "usage_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("review_id", sa.String(length=36), nullable=False),
        sa.Column("step_key", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_id", sa.String(length=128), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reasoning_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usd_micros", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("eur_micros", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_status", sa.String(length=32), nullable=False),
        sa.Column("result_status", sa.String(length=32), nullable=False),
        sa.Column("detail_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_usage_records_review_id", "usage_records", ["review_id"])
    op.create_table(
        "real_pipeline_lock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("review_id", sa.String(length=36), nullable=True),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("real_pipeline_lock")
    op.drop_index("ix_usage_records_review_id", table_name="usage_records")
    op.drop_table("usage_records")
    op.drop_index("ix_budget_reservations_review_id", table_name="budget_reservations")
    op.drop_table("budget_reservations")
    op.drop_table("budget_periods")
    op.drop_index("ix_tech_pipeline_steps_review_id", table_name="tech_pipeline_steps")
    op.drop_table("tech_pipeline_steps")
    op.drop_column("tech_reviews", "frozen_models_json")
    op.drop_column("tech_reviews", "failure_message")
    op.drop_column("tech_reviews", "envelope_eur_micros")
    op.drop_column("tech_reviews", "envelope_usd_micros")
    op.drop_column("tech_reviews", "plan_json")
    op.drop_column("tech_reviews", "execution_mode")
