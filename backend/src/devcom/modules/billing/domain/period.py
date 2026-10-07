from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")


def budget_month_id(moment_utc: datetime) -> str:
    """Return YYYY-MM for Europe/Paris calendar month of an aware UTC datetime."""
    local = moment_utc.astimezone(PARIS)
    return f"{local.year:04d}-{local.month:02d}"


def month_bounds(month_id: str) -> tuple[date, date]:
    year_s, month_s = month_id.split("-")
    year, month = int(year_s), int(month_s)
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end
