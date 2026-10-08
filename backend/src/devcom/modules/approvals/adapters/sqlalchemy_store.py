from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.approvals.adapters.sqlalchemy_models import ApprovalRequestRow
from devcom.modules.approvals.domain.approval import ApprovalRequest
from devcom.modules.approvals.domain.status import ApprovalStatus


class SqlAlchemyApprovalStore:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def get(self, approval_id: str) -> ApprovalRequest | None:
        with self._sessions() as session:
            row = session.get(ApprovalRequestRow, approval_id)
            return None if row is None else _from_row(row)

    def get_by_idempotency(self, key: str) -> ApprovalRequest | None:
        with self._sessions() as session:
            row = session.scalars(
                select(ApprovalRequestRow).where(ApprovalRequestRow.idempotency_key == key)
            ).first()
            return None if row is None else _from_row(row)

    def save(self, approval: ApprovalRequest) -> None:
        with self._sessions() as session:
            row = session.get(ApprovalRequestRow, approval.id)
            payload = _to_row(approval)
            if row is None:
                session.add(payload)
            else:
                for col in payload.__table__.columns.keys():
                    if col == "id":
                        continue
                    setattr(row, col, getattr(payload, col))
            session.commit()

    def invalidate_open_for_target(
        self,
        *,
        target_id: str,
        action_id: str,
        now: datetime,
    ) -> None:
        with self._sessions() as session:
            rows = session.scalars(
                select(ApprovalRequestRow).where(
                    ApprovalRequestRow.target_id == target_id,
                    ApprovalRequestRow.action_id == action_id,
                    ApprovalRequestRow.status.in_(
                        [ApprovalStatus.PENDING.value, ApprovalStatus.GRANTED.value]
                    ),
                )
            ).all()
            for row in rows:
                row.status = ApprovalStatus.INVALIDATED.value
                row.decided_at = now
            session.commit()


def _to_row(item: ApprovalRequest) -> ApprovalRequestRow:
    return ApprovalRequestRow(
        id=item.id,
        action_id=item.action_id,
        target_id=item.target_id,
        payload_hash=item.payload_hash,
        resource_version=item.resource_version,
        status=item.status.value,
        author=item.author,
        created_at=item.created_at,
        expires_at=item.expires_at,
        decided_at=item.decided_at,
        consumed_at=item.consumed_at,
        idempotency_key=item.idempotency_key,
    )


def _from_row(row: ApprovalRequestRow) -> ApprovalRequest:
    return ApprovalRequest(
        id=row.id,
        action_id=row.action_id,
        target_id=row.target_id,
        payload_hash=row.payload_hash,
        resource_version=row.resource_version,
        status=ApprovalStatus(row.status),
        author=row.author,
        created_at=_aware(row.created_at),
        expires_at=_aware(row.expires_at),
        decided_at=_aware_opt(row.decided_at),
        consumed_at=_aware_opt(row.consumed_at),
        idempotency_key=row.idempotency_key,
    )


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _aware_opt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _aware(value)
