from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.missions.tech.adapters.review_row_mapper import (
    copy_row,
    from_row,
    to_row,
    upsert_decision,
)
from devcom.modules.missions.tech.adapters.sqlalchemy_models import (
    IdempotencyRow,
    TechReviewRow,
)
from devcom.modules.missions.tech.domain.errors import TechConflictError
from devcom.modules.missions.tech.domain.review import TechReview


class SqlAlchemyTechReviewRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save_atomic(
        self,
        review: TechReview,
        *,
        idem_operation: str | None = None,
        idem_key: str | None = None,
        idem_hash: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            try:
                self._persist(session, review)
                if idem_operation and idem_key and idem_hash:
                    session.add(
                        IdempotencyRow(
                            id=str(uuid4()),
                            operation=idem_operation,
                            key=idem_key,
                            payload_hash=idem_hash,
                            resource_id=review.id,
                        )
                    )
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise TechConflictError("concurrent write rejected") from exc

    def get_by_id(self, review_id: str) -> TechReview | None:
        with self._session_factory() as session:
            row = session.get(TechReviewRow, review_id)
            if row is None:
                return None
            return from_row(session, row)

    def list_all(self) -> list[TechReview]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(TechReviewRow).order_by(TechReviewRow.updated_at.desc())
            ).all()
            return [from_row(session, row) for row in rows]

    def get_by_create_key(self, key: str) -> TechReview | None:
        with self._session_factory() as session:
            row = session.scalars(
                select(TechReviewRow).where(TechReviewRow.create_idempotency_key == key)
            ).first()
            if row is None:
                return None
            return from_row(session, row)

    def _persist(self, session: Session, review: TechReview) -> None:
        row = session.get(TechReviewRow, review.id)
        payload = to_row(review)
        if row is None:
            session.add(payload)
        else:
            copy_row(payload, row)
        upsert_decision(session, review)


class SqlIdempotencyStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get(self, operation: str, key: str) -> tuple[str, str] | None:
        with self._session_factory() as session:
            row = session.scalars(
                select(IdempotencyRow).where(
                    IdempotencyRow.operation == operation,
                    IdempotencyRow.key == key,
                )
            ).first()
            if row is None:
                return None
            return row.payload_hash, row.resource_id

    def put(self, operation: str, key: str, payload_hash: str, resource_id: str) -> None:
        with self._session_factory() as session:
            session.add(
                IdempotencyRow(
                    id=str(uuid4()),
                    operation=operation,
                    key=key,
                    payload_hash=payload_hash,
                    resource_id=resource_id,
                )
            )
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise TechConflictError("idempotency key conflict") from exc
