from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.adapters.sqlalchemy_events import SqlAlchemyEventStore
from devcom.modules.missions.tech.application.idempotency import (
    payload_hash,
    resolve_idempotency,
)
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.domain.errors import (
    TechNotFoundError,
    TechValidationError,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import IDEM_ACK_UNCERTAIN
from devcom.modules.missions.tech.ports.idempotency_store import IdempotencyStore
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
from devcom.shared.time import Clock

REASON_MIN = 1
REASON_MAX = 500


@dataclass(frozen=True, slots=True)
class AcknowledgeUncertaintyCommand:
    review_id: str
    reason: str
    idempotency_key: str


class AcknowledgeUncertainty:
    """Human acknowledgement of uncertainty — does not settle ambiguous budget."""

    def __init__(
        self,
        *,
        repository: TechReviewRepository,
        events: SqlAlchemyEventStore,
        policy: PermissionPolicy,
        idempotency: IdempotencyStore,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._events = events
        self._policy = policy
        self._idempotency = idempotency
        self._clock = clock

    def execute(self, command: AcknowledgeUncertaintyCommand) -> TechReview:
        require_tech_action(self._policy, "tech.review.run")
        reason = command.reason.strip()
        if not (REASON_MIN <= len(reason) <= REASON_MAX):
            raise TechValidationError(
                f"reason must be {REASON_MIN} to {REASON_MAX} characters after trim"
            )
        if not command.idempotency_key.strip():
            raise TechValidationError("idempotency key is required")
        digest = payload_hash({"review_id": command.review_id, "reason": reason})
        existing = resolve_idempotency(
            self._idempotency,
            operation=IDEM_ACK_UNCERTAIN,
            key=command.idempotency_key,
            expected_hash=digest,
        )
        if existing is not None:
            return self._require(existing)
        review = self._require(command.review_id)
        now = self._clock.now()
        review.acknowledge_uncertainty(reason=reason, now=now)
        self._repository.save_atomic(
            review,
            idem_operation=IDEM_ACK_UNCERTAIN,
            idem_key=command.idempotency_key,
            idem_hash=digest,
        )
        self._events.append(
            review_id=review.id,
            event_type="uncertainty.acknowledged",
            dedupe_key=f"uncertainty.acknowledged:{command.idempotency_key}",
            payload={"reason_len": len(reason)},
            occurred_at=now,
        )
        return self._require(review.id)

    def _require(self, review_id: str) -> TechReview:
        review = self._repository.get_by_id(review_id)
        if review is None:
            raise TechNotFoundError(f"tech review {review_id} not found")
        return review
