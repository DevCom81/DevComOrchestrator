from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.billing.adapters import sqlalchemy_models as _billing  # noqa: F401
from devcom.modules.billing.adapters.sqlalchemy_ledger import SqlAlchemyBudgetLedger
from devcom.modules.billing.domain.errors import BudgetExceededError
from devcom.modules.missions.adapters import sqlalchemy_models as _missions  # noqa: F401
from devcom.modules.missions.tech.adapters import sqlalchemy_models as _tech  # noqa: F401
from devcom.modules.projects.adapters import sqlalchemy_models as _projects  # noqa: F401
from devcom.shared.persistence import Base

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


@pytest.fixture()
def ledger(tmp_path: Path) -> SqlAlchemyBudgetLedger:
    engine = create_engine(f"sqlite:///{tmp_path / 'b.sqlite'}")

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection: object, _record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, class_=Session)
    return SqlAlchemyBudgetLedger(sessions, monthly_cap=300_000)


def test_concurrent_envelopes_cannot_overdraw(ledger: SqlAlchemyBudgetLedger) -> None:
    ledger.reserve_review_envelope(
        review_id="r1",
        envelope_usd_micros=200_000,
        envelope_eur_micros=200_000,
        fx_rate="0.88739",
        fx_rate_date="2026-10-06",
        fx_margin_ratio="0.05",
        rates_verified_at="2026-10-07",
        now=NOW,
    )
    with pytest.raises(BudgetExceededError):
        ledger.reserve_review_envelope(
            review_id="r2",
            envelope_usd_micros=200_000,
            envelope_eur_micros=200_000,
            fx_rate="0.88739",
            fx_rate_date="2026-10-06",
            fx_margin_ratio="0.05",
            rates_verified_at="2026-10-07",
            now=NOW,
        )


def test_confirmed_usage_moves_from_reserved_without_double_count(
    ledger: SqlAlchemyBudgetLedger,
) -> None:
    ledger.reserve_review_envelope(
        review_id="r1",
        envelope_usd_micros=100_000,
        envelope_eur_micros=100_000,
        fx_rate="0.88739",
        fx_rate_date="2026-10-06",
        fx_margin_ratio="0.05",
        rates_verified_at="2026-10-07",
        now=NOW,
    )
    ledger.record_usage(
        review_id="r1",
        step_key="analyze:architecte",
        provider="openai",
        model_id="gpt-6.1-sol",
        input_tokens=10,
        output_tokens=5,
        reasoning_tokens=2,
        usd_micros=1000,
        eur_micros=40_000,
        cost_status="confirmed",
        result_status="invalid",
        now=NOW,
    )
    summary = ledger.summary("2026-10")
    assert summary["confirmed_eur_micros"] == 40_000
    assert summary["reserved_eur_micros"] == 60_000
    assert int(summary["confirmed_eur_micros"]) + int(summary["reserved_eur_micros"]) == 100_000


def test_release_unused_envelope_settles_and_frees_remainder(
    ledger: SqlAlchemyBudgetLedger,
) -> None:
    ledger.reserve_review_envelope(
        review_id="r-settle",
        envelope_usd_micros=100_000,
        envelope_eur_micros=100_000,
        fx_rate="0.88739",
        fx_rate_date="2026-10-06",
        fx_margin_ratio="0.05",
        rates_verified_at="2026-10-07",
        now=NOW,
    )
    ledger.record_usage(
        review_id="r-settle",
        step_key="synthesize",
        provider="openai",
        model_id="gpt-6.1-sol",
        input_tokens=10,
        output_tokens=5,
        reasoning_tokens=0,
        usd_micros=500,
        eur_micros=25_000,
        cost_status="confirmed",
        result_status="ok",
        now=NOW,
    )
    ledger.release_unused_envelope("r-settle")
    summary = ledger.summary("2026-10")
    reservation = ledger.reservation_for("r-settle")
    assert reservation is not None
    assert reservation["status"] == "settled"
    assert summary["confirmed_eur_micros"] == 25_000
    assert summary["reserved_eur_micros"] == 0
