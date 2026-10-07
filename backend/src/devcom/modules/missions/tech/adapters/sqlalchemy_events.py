from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.missions.tech.adapters.sqlalchemy_models import TechReviewEventRow

MAX_PAGE = 100


class SqlAlchemyEventStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sessions = session_factory

    def append(
        self,
        *,
        review_id: str,
        event_type: str,
        dedupe_key: str,
        payload: dict[str, object],
        occurred_at: datetime,
        session: Session | None = None,
    ) -> int | None:
        """Insert event; return seq or None if dedupe hit. Optional external session."""
        if session is not None:
            return self._append_on(session, review_id, event_type, dedupe_key, payload, occurred_at)
        with self._sessions() as own:
            seq = self._append_on(own, review_id, event_type, dedupe_key, payload, occurred_at)
            try:
                own.commit()
            except IntegrityError:
                own.rollback()
                return None
            return seq

    def list_after(self, review_id: str, after_seq: int, limit: int = 50) -> list[dict[str, Any]]:
        page = max(1, min(limit, MAX_PAGE))
        with self._sessions() as session:
            rows = session.scalars(
                select(TechReviewEventRow)
                .where(
                    TechReviewEventRow.review_id == review_id,
                    TechReviewEventRow.seq > after_seq,
                )
                .order_by(TechReviewEventRow.seq)
                .limit(page)
            ).all()
            return [_to_dict(row) for row in rows]

    def latest_seq(self, review_id: str) -> int:
        with self._sessions() as session:
            value = session.scalar(
                select(func.max(TechReviewEventRow.seq)).where(
                    TechReviewEventRow.review_id == review_id
                )
            )
            return int(value or 0)

    def _append_on(
        self,
        session: Session,
        review_id: str,
        event_type: str,
        dedupe_key: str,
        payload: dict[str, object],
        occurred_at: datetime,
    ) -> int | None:
        existing = session.scalars(
            select(TechReviewEventRow).where(
                TechReviewEventRow.review_id == review_id,
                TechReviewEventRow.dedupe_key == dedupe_key,
            )
        ).first()
        if existing is not None:
            return None
        current = session.scalar(
            select(func.max(TechReviewEventRow.seq)).where(
                TechReviewEventRow.review_id == review_id
            )
        )
        seq = int(current or 0) + 1
        session.add(
            TechReviewEventRow(
                id=str(uuid4()),
                review_id=review_id,
                seq=seq,
                event_type=event_type,
                dedupe_key=dedupe_key,
                occurred_at=occurred_at,
                payload_json=json.dumps(payload, ensure_ascii=False),
            )
        )
        return seq


def _to_dict(row: TechReviewEventRow) -> dict[str, Any]:
    return {
        "id": row.id,
        "review_id": row.review_id,
        "seq": row.seq,
        "event_type": row.event_type,
        "occurred_at": row.occurred_at.isoformat(),
        "payload": json.loads(row.payload_json),
    }
