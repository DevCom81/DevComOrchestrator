from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from devcom.modules.approvals.domain.errors import ApprovalConflictError, ApprovalValidationError
from devcom.modules.approvals.domain.status import (
    GO_TTL_HOURS,
    LOCAL_AUTHOR,
    ApprovalStatus,
)


@dataclass(slots=True)
class ApprovalRequest:
    id: str
    action_id: str
    target_id: str
    payload_hash: str
    resource_version: int
    status: ApprovalStatus
    author: str
    created_at: datetime
    expires_at: datetime
    decided_at: datetime | None = None
    consumed_at: datetime | None = None
    idempotency_key: str | None = None

    @classmethod
    def create(
        cls,
        *,
        action_id: str,
        target_id: str,
        payload_hash: str,
        resource_version: int,
        now: datetime,
        idempotency_key: str | None = None,
        ttl_hours: int = GO_TTL_HOURS,
    ) -> ApprovalRequest:
        if not action_id.strip() or not target_id.strip():
            raise ApprovalValidationError("action_id and target_id are required")
        if len(payload_hash) != 64:
            raise ApprovalValidationError("payload_hash must be sha256 hex")
        if resource_version < 1:
            raise ApprovalValidationError("resource_version must be >= 1")
        stamp = _utc(now)
        return cls(
            id=str(uuid4()),
            action_id=action_id.strip(),
            target_id=target_id.strip(),
            payload_hash=payload_hash,
            resource_version=resource_version,
            status=ApprovalStatus.PENDING,
            author=LOCAL_AUTHOR,
            created_at=stamp,
            expires_at=stamp + timedelta(hours=ttl_hours),
            idempotency_key=idempotency_key,
        )

    def grant(self, now: datetime) -> None:
        self._ensure_pending(now)
        self.status = ApprovalStatus.GRANTED
        self.decided_at = _utc(now)

    def refuse(self, now: datetime) -> None:
        self._ensure_pending(now)
        self.status = ApprovalStatus.REFUSED
        self.decided_at = _utc(now)

    def invalidate(self, now: datetime) -> None:
        if self.status in {ApprovalStatus.CONSUMED, ApprovalStatus.REFUSED}:
            return
        if self.status in {ApprovalStatus.PENDING, ApprovalStatus.GRANTED}:
            self.status = ApprovalStatus.INVALIDATED
            self.decided_at = _utc(now)

    def mark_expired(self, now: datetime) -> None:
        if self.status in {ApprovalStatus.PENDING, ApprovalStatus.GRANTED}:
            if _utc(now) >= self.expires_at:
                self.status = ApprovalStatus.EXPIRED

    def consume_for_export(
        self,
        *,
        payload_hash: str,
        resource_version: int,
        now: datetime,
    ) -> None:
        stamp = _utc(now)
        if stamp >= self.expires_at:
            self.status = ApprovalStatus.EXPIRED
            raise ApprovalConflictError("approval expired — cannot create new export")
        if self.status != ApprovalStatus.GRANTED:
            raise ApprovalConflictError(f"approval status is {self.status.value}")
        if self.payload_hash != payload_hash or self.resource_version != resource_version:
            raise ApprovalConflictError("approval does not match current package")
        self.status = ApprovalStatus.CONSUMED
        self.consumed_at = stamp

    def _ensure_pending(self, now: datetime) -> None:
        stamp = _utc(now)
        if stamp >= self.expires_at:
            self.status = ApprovalStatus.EXPIRED
            raise ApprovalConflictError("approval expired")
        if self.status != ApprovalStatus.PENDING:
            raise ApprovalConflictError(f"approval status is {self.status.value}")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ApprovalValidationError("timestamps must be timezone-aware UTC")
    return value.astimezone(UTC)
