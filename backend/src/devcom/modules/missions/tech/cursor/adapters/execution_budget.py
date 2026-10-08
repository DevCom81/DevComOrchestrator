from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.billing.adapters.sqlalchemy_models import BudgetPeriodRow
from devcom.modules.billing.domain.errors import BudgetExceededError
from devcom.modules.billing.domain.period import budget_month_id
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_models import (
    CursorExecutionReservationRow,
)


class ExecutionBudgetGate:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        *,
        monthly_cap: int,
    ) -> None:
        self._sessions = sessions
        self._monthly_cap = monthly_cap

    def reserve(self, *, execution_id: str, eur_micros: int, now: datetime) -> None:
        month_id = budget_month_id(now)
        with self._sessions() as session:
            existing = session.get(CursorExecutionReservationRow, execution_id)
            if existing is not None:
                return
            period = session.get(BudgetPeriodRow, month_id)
            if period is None:
                period = BudgetPeriodRow(
                    month_id=month_id,
                    cap_eur_micros=self._monthly_cap,
                    confirmed_eur_micros=0,
                    reserved_eur_micros=0,
                    uncertain_eur_micros=0,
                )
                session.add(period)
                session.flush()
            committed = (
                period.confirmed_eur_micros
                + period.reserved_eur_micros
                + period.uncertain_eur_micros
            )
            if committed + eur_micros > period.cap_eur_micros:
                raise BudgetExceededError("monthly budget cap would be exceeded")
            period.reserved_eur_micros += eur_micros
            session.add(
                CursorExecutionReservationRow(
                    execution_id=execution_id,
                    month_id=month_id,
                    reserved_eur_micros=eur_micros,
                    created_at=now,
                )
            )
            session.commit()

    def release_unused(self, *, execution_id: str) -> None:
        with self._sessions() as session:
            row = session.get(CursorExecutionReservationRow, execution_id)
            if row is None:
                return
            period = session.get(BudgetPeriodRow, row.month_id)
            if period is not None:
                period.reserved_eur_micros = max(
                    0, period.reserved_eur_micros - row.reserved_eur_micros
                )
            session.delete(row)
            session.commit()

    def mark_uncertain(self, *, execution_id: str) -> None:
        """Keep reservation held as uncertain when Cursor cost unknown."""
        with self._sessions() as session:
            row = session.get(CursorExecutionReservationRow, execution_id)
            if row is None:
                return
            period = session.get(BudgetPeriodRow, row.month_id)
            if period is None:
                return
            amount = row.reserved_eur_micros
            period.reserved_eur_micros = max(0, period.reserved_eur_micros - amount)
            period.uncertain_eur_micros += amount
            session.delete(row)
            session.commit()


def list_open_execution_reservations(sessions: sessionmaker[Session]) -> list[str]:
    with sessions() as session:
        rows = session.scalars(select(CursorExecutionReservationRow)).all()
        return [row.execution_id for row in rows]
