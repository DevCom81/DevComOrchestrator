from __future__ import annotations

from datetime import UTC, datetime

from devcom.modules.billing.domain.period import budget_month_id


def test_budget_month_europe_paris_crosses_utc_midnight() -> None:
    # 2026-10-31 23:30 UTC → 2026-11-01 00:30 Paris (CEST ended? Oct 31 still CEST UTC+2)
    late_october = datetime(2026, 10, 31, 21, 30, tzinfo=UTC)  # 23:30 Paris
    assert budget_month_id(late_october) == "2026-10"
    early_november = datetime(2026, 10, 31, 23, 0, tzinfo=UTC)  # 01:00 Paris Nov 1
    assert budget_month_id(early_november) == "2026-11"
