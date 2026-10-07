from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.billing.adapters.sqlalchemy_models import RealPipelineLockRow


class PipelineLockStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sessions = session_factory

    def try_acquire(self, review_id: str, now: datetime) -> bool:
        with self._sessions() as session:
            row = session.get(RealPipelineLockRow, 1)
            if row is None:
                session.add(RealPipelineLockRow(id=1, review_id=review_id, acquired_at=now))
                session.commit()
                return True
            if row.review_id is None or row.review_id == review_id:
                row.review_id = review_id
                row.acquired_at = now
                session.commit()
                return True
            return False

    def release(self, review_id: str) -> None:
        with self._sessions() as session:
            row = session.get(RealPipelineLockRow, 1)
            if row is not None and row.review_id == review_id:
                row.review_id = None
                row.acquired_at = None
                session.commit()

    def clear(self) -> None:
        with self._sessions() as session:
            row = session.get(RealPipelineLockRow, 1)
            if row is not None:
                row.review_id = None
                row.acquired_at = None
                session.commit()
