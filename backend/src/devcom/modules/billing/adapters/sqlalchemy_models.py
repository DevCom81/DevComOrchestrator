from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from devcom.shared.persistence import Base


class BudgetPeriodRow(Base):
    __tablename__ = "budget_periods"

    month_id: Mapped[str] = mapped_column(String(7), primary_key=True)
    cap_eur_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    confirmed_eur_micros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_eur_micros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uncertain_eur_micros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class BudgetReservationRow(Base):
    __tablename__ = "budget_reservations"
    __table_args__ = (UniqueConstraint("review_id", name="uq_budget_reservations_review"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    month_id: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    envelope_usd_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    envelope_eur_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    confirmed_usd_micros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_eur_micros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fx_rate: Mapped[str] = mapped_column(String(32), nullable=False)
    fx_rate_date: Mapped[str] = mapped_column(String(32), nullable=False)
    fx_margin_ratio: Mapped[str] = mapped_column(String(32), nullable=False)
    rates_verified_at: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UsageRecordRow(Base):
    __tablename__ = "usage_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    step_key: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reasoning_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usd_micros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eur_micros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_status: Mapped[str] = mapped_column(String(32), nullable=False)
    result_status: Mapped[str] = mapped_column(String(32), nullable=False)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RealPipelineLockRow(Base):
    __tablename__ = "real_pipeline_lock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    acquired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
