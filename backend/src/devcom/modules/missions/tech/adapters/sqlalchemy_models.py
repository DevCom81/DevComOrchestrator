from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from devcom.shared.persistence import Base


class TechReviewRow(Base):
    __tablename__ = "tech_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    request_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    unmatched_request: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scenario_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    scenario_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scenario_label_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyses_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    challenges_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    synthesis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposals_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposals_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    capability_registry_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    permission_policy_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blocking_policy_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    create_idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        unique=True,
    )
    execution_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    envelope_usd_micros: Mapped[int | None] = mapped_column(Integer, nullable=True)
    envelope_eur_micros: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    frozen_models_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    code_snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    uncertainty_ack_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    uncertainty_ack_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class TechReviewEventRow(Base):
    __tablename__ = "tech_review_events"
    __table_args__ = (
        UniqueConstraint("review_id", "seq", name="uq_tech_review_events_seq"),
        UniqueConstraint("review_id", "dedupe_key", name="uq_tech_review_events_dedupe"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tech_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(128), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class TechPipelineStepRow(Base):
    __tablename__ = "tech_pipeline_steps"
    __table_args__ = (
        UniqueConstraint("review_id", "step_key", name="uq_tech_pipeline_steps"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tech_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_key: Mapped[str] = mapped_column(String(128), nullable=False)
    phase: Mapped[str] = mapped_column(String(32), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    optional: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_status: Mapped[str | None] = mapped_column(String(32), nullable=True)



class TechDecisionRow(Base):
    __tablename__ = "tech_decisions"
    __table_args__ = (UniqueConstraint("review_id", name="uq_tech_decisions_review"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tech_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    proposal_id: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_version: Mapped[int] = mapped_column(Integer, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(128), nullable=False)
    decided_at: Mapped[str] = mapped_column(String(64), nullable=False)


class TechAdrRow(Base):
    __tablename__ = "tech_adrs"
    __table_args__ = (UniqueConstraint("review_id", name="uq_tech_adrs_review"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tech_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    demo_warning: Mapped[str] = mapped_column(Text, nullable=False)


class IdempotencyRow(Base):
    __tablename__ = "tech_idempotency"
    __table_args__ = (
        UniqueConstraint("operation", "key", name="uq_tech_idempotency_op_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
