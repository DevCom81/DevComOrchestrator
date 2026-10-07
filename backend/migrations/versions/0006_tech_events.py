"""Tech review event journal and uncertainty acknowledgement.

Revision ID: 0006_tech_events
Revises: 0005_code_context
Create Date: 2026-10-07

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_tech_events"
down_revision: Union[str, None] = "0005_code_context"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tech_review_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("review_id", sa.String(length=36), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("dedupe_key", sa.String(length=128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["tech_reviews.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("review_id", "seq", name="uq_tech_review_events_seq"),
        sa.UniqueConstraint("review_id", "dedupe_key", name="uq_tech_review_events_dedupe"),
    )
    op.create_index("ix_tech_review_events_review_id", "tech_review_events", ["review_id"])
    with op.batch_alter_table("tech_reviews") as batch:
        batch.add_column(sa.Column("uncertainty_ack_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("uncertainty_ack_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tech_reviews") as batch:
        batch.drop_column("uncertainty_ack_reason")
        batch.drop_column("uncertainty_ack_at")
    op.drop_index("ix_tech_review_events_review_id", table_name="tech_review_events")
    op.drop_table("tech_review_events")
