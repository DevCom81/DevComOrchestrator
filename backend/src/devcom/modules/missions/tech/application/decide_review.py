from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.adr_builder import build_adr_body
from devcom.modules.missions.tech.application.idempotency import (
    payload_hash,
    resolve_idempotency,
)
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.domain.errors import (
    TechConflictError,
    TechNotFoundError,
    TechValidationError,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import IDEM_DECIDE
from devcom.modules.missions.tech.ports.idempotency_store import IdempotencyStore
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class DecideTechReviewCommand:
    review_id: str
    proposal_id: str
    proposal_version: int
    rationale: str
    idempotency_key: str


class DecideTechReview:
    def __init__(
        self,
        repository: TechReviewRepository,
        policy: PermissionPolicy,
        idempotency: IdempotencyStore,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._policy = policy
        self._idempotency = idempotency
        self._clock = clock

    def execute(self, command: DecideTechReviewCommand) -> TechReview:
        require_tech_action(self._policy, "tech.review.decide")
        if not command.idempotency_key.strip():
            raise TechValidationError("idempotency key is required")
        digest = payload_hash(
            {
                "review_id": command.review_id,
                "proposal_id": command.proposal_id,
                "proposal_version": command.proposal_version,
                "rationale": command.rationale.strip(),
            }
        )
        existing_id = resolve_idempotency(
            self._idempotency,
            operation=IDEM_DECIDE,
            key=command.idempotency_key,
            expected_hash=digest,
        )
        if existing_id is not None:
            return self._require(existing_id)
        return self._apply(command, digest)

    def _apply(self, command: DecideTechReviewCommand, digest: str) -> TechReview:
        review = self._require(command.review_id)
        chosen = next(
            (item for item in review.proposals if item.id == command.proposal_id),
            None,
        )
        if chosen is None:
            raise TechValidationError(f"unknown proposal `{command.proposal_id}`")
        review.decide(
            proposal_id=command.proposal_id,
            proposal_version=command.proposal_version,
            rationale=command.rationale,
            now=self._clock.now(),
            adr_body=build_adr_body(review, chosen, command.rationale.strip()),
        )
        try:
            self._repository.save_atomic(
                review,
                idem_operation=IDEM_DECIDE,
                idem_key=command.idempotency_key,
                idem_hash=digest,
            )
        except TechConflictError:
            return self._reconcile_conflict(command)
        return self._require(command.review_id)

    def _reconcile_conflict(self, command: DecideTechReviewCommand) -> TechReview:
        reloaded = self._require(command.review_id)
        if (
            reloaded.decision is not None
            and reloaded.decision.proposal_id == command.proposal_id
        ):
            return reloaded
        raise TechConflictError("review already has a different decision")

    def _require(self, review_id: str) -> TechReview:
        review = self._repository.get_by_id(review_id)
        if review is None:
            raise TechNotFoundError(f"tech review {review_id} not found")
        return review
