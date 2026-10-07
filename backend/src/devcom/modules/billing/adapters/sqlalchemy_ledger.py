from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.billing.adapters.pipeline_lock import PipelineLockStore
from devcom.modules.billing.adapters.sqlalchemy_models import (
    BudgetPeriodRow,
    BudgetReservationRow,
    UsageRecordRow,
)
from devcom.modules.billing.domain.errors import BudgetConflictError, BudgetExceededError
from devcom.modules.billing.domain.period import budget_month_id


class SqlAlchemyBudgetLedger:
    def __init__(self, session_factory: sessionmaker[Session], monthly_cap: int) -> None:
        self._sessions = session_factory
        self._monthly_cap = monthly_cap
        self._locks = PipelineLockStore(session_factory)

    def reserve_review_envelope(
        self,
        *,
        review_id: str,
        envelope_usd_micros: int,
        envelope_eur_micros: int,
        fx_rate: str,
        fx_rate_date: str,
        fx_margin_ratio: str,
        rates_verified_at: str,
        now: datetime,
    ) -> str:
        month_id = budget_month_id(now)
        with self._sessions() as session:
            period = self._period(session, month_id)
            committed = (
                period.confirmed_eur_micros
                + period.reserved_eur_micros
                + period.uncertain_eur_micros
            )
            if committed + envelope_eur_micros > period.cap_eur_micros:
                raise BudgetExceededError("monthly budget cap would be exceeded")
            existing = session.scalars(
                select(BudgetReservationRow).where(BudgetReservationRow.review_id == review_id)
            ).first()
            if existing is not None:
                held = existing.status == "held"
                same = existing.envelope_eur_micros == envelope_eur_micros
                if held and same:
                    return existing.id
                raise BudgetConflictError("review already has a budget reservation")
            reservation_id = str(uuid4())
            session.add(
                BudgetReservationRow(
                    id=reservation_id,
                    review_id=review_id,
                    month_id=month_id,
                    status="held",
                    envelope_usd_micros=envelope_usd_micros,
                    envelope_eur_micros=envelope_eur_micros,
                    confirmed_usd_micros=0,
                    confirmed_eur_micros=0,
                    fx_rate=fx_rate,
                    fx_rate_date=fx_rate_date,
                    fx_margin_ratio=fx_margin_ratio,
                    rates_verified_at=rates_verified_at,
                    created_at=now,
                )
            )
            period.reserved_eur_micros += envelope_eur_micros
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise BudgetConflictError("reservation conflict") from exc
            return reservation_id

    def record_usage(
        self,
        *,
        review_id: str,
        step_key: str,
        provider: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        reasoning_tokens: int,
        usd_micros: int,
        eur_micros: int,
        cost_status: str,
        result_status: str,
        now: datetime,
        detail_json: str | None = None,
    ) -> None:
        with self._sessions() as session:
            reservation = session.scalars(
                select(BudgetReservationRow).where(BudgetReservationRow.review_id == review_id)
            ).first()
            if reservation is None:
                raise BudgetConflictError("missing reservation for review")
            period = self._period(session, reservation.month_id)
            session.add(
                UsageRecordRow(
                    id=str(uuid4()),
                    review_id=review_id,
                    step_key=step_key,
                    provider=provider,
                    model_id=model_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    reasoning_tokens=reasoning_tokens,
                    usd_micros=usd_micros,
                    eur_micros=eur_micros,
                    cost_status=cost_status,
                    result_status=result_status,
                    detail_json=detail_json,
                    created_at=now,
                )
            )
            _apply_cost_to_period(
                reservation, period, cost_status, usd_micros=usd_micros, eur_micros=eur_micros
            )
            session.commit()

    def release_unused_envelope(self, review_id: str) -> None:
        with self._sessions() as session:
            reservation = session.scalars(
                select(BudgetReservationRow).where(BudgetReservationRow.review_id == review_id)
            ).first()
            if reservation is None or reservation.status not in {"held", "overrun"}:
                return
            period = self._period(session, reservation.month_id)
            unused = max(0, reservation.envelope_eur_micros - reservation.confirmed_eur_micros)
            period.reserved_eur_micros = max(0, period.reserved_eur_micros - unused)
            reservation.status = "settled" if reservation.status != "overrun" else "overrun"
            session.commit()

    def is_overrun(self, review_id: str) -> bool:
        with self._sessions() as session:
            reservation = session.scalars(
                select(BudgetReservationRow).where(BudgetReservationRow.review_id == review_id)
            ).first()
            return reservation is not None and reservation.status == "overrun"

    def summary(self, month_id: str) -> dict[str, int | str]:
        with self._sessions() as session:
            period = self._period(session, month_id)
            return {
                "month_id": period.month_id,
                "cap_eur_micros": period.cap_eur_micros,
                "confirmed_eur_micros": period.confirmed_eur_micros,
                "reserved_eur_micros": period.reserved_eur_micros,
                "uncertain_eur_micros": period.uncertain_eur_micros,
            }

    def list_usage(self, review_id: str) -> list[dict[str, object]]:
        with self._sessions() as session:
            rows = session.scalars(
                select(UsageRecordRow)
                .where(UsageRecordRow.review_id == review_id)
                .order_by(UsageRecordRow.created_at)
            ).all()
            return [
                {
                    "step_key": row.step_key,
                    "provider": row.provider,
                    "model_id": row.model_id,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "reasoning_tokens": row.reasoning_tokens,
                    "usd_micros": row.usd_micros,
                    "eur_micros": row.eur_micros,
                    "cost_status": row.cost_status,
                    "result_status": row.result_status,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]

    def reservation_for(self, review_id: str) -> dict[str, object] | None:
        with self._sessions() as session:
            row = session.scalars(
                select(BudgetReservationRow).where(BudgetReservationRow.review_id == review_id)
            ).first()
            if row is None:
                return None
            return {
                "id": row.id,
                "month_id": row.month_id,
                "status": row.status,
                "envelope_usd_micros": row.envelope_usd_micros,
                "envelope_eur_micros": row.envelope_eur_micros,
                "confirmed_usd_micros": row.confirmed_usd_micros,
                "confirmed_eur_micros": row.confirmed_eur_micros,
                "fx_rate": row.fx_rate,
                "fx_rate_date": row.fx_rate_date,
                "fx_margin_ratio": row.fx_margin_ratio,
                "rates_verified_at": row.rates_verified_at,
            }

    def try_acquire_global_lock(self, review_id: str, now: datetime) -> bool:
        return self._locks.try_acquire(review_id, now)

    def release_global_lock(self, review_id: str) -> None:
        self._locks.release(review_id)

    def clear_stale_lock(self) -> None:
        self._locks.clear()

    def _period(self, session: Session, month_id: str) -> BudgetPeriodRow:
        row = session.get(BudgetPeriodRow, month_id)
        if row is None:
            row = BudgetPeriodRow(
                month_id=month_id,
                cap_eur_micros=self._monthly_cap,
                confirmed_eur_micros=0,
                reserved_eur_micros=0,
                uncertain_eur_micros=0,
            )
            session.add(row)
            session.flush()
        return row


def _apply_cost_to_period(
    reservation: BudgetReservationRow,
    period: BudgetPeriodRow,
    cost_status: str,
    *,
    usd_micros: int,
    eur_micros: int,
) -> None:
    if cost_status == "confirmed":
        previously = reservation.confirmed_eur_micros
        reservation.confirmed_usd_micros += usd_micros
        reservation.confirmed_eur_micros += eur_micros
        period.confirmed_eur_micros += eur_micros
        covered = min(eur_micros, max(0, reservation.envelope_eur_micros - previously))
        period.reserved_eur_micros = max(0, period.reserved_eur_micros - covered)
        if reservation.confirmed_eur_micros > reservation.envelope_eur_micros:
            reservation.status = "overrun"
        return
    if cost_status == "uncertain" and eur_micros > 0:
        period.uncertain_eur_micros += eur_micros
        period.reserved_eur_micros = max(0, period.reserved_eur_micros - eur_micros)
