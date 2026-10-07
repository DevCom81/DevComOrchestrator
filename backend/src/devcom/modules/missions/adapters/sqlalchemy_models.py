from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from devcom.shared.persistence import Base


class MissionRow(Base):
    __tablename__ = "missions"

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
    routing_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    routing_disclaimer: Mapped[str | None] = mapped_column(Text, nullable=True)
    routing_rule_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    routing_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    capability_registry_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    permission_policy_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dispatch_rules_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clarification_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    clarification_questions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_block_action_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    auth_block_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_block_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)


class MissionTaskRow(Base):
    __tablename__ = "mission_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    mission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capability_id: Mapped[str] = mapped_column(String(128), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
