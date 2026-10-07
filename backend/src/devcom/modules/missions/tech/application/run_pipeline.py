from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.domain.capability import CapabilityRegistry
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.adapters.scenario_catalog import ScenarioCatalog
from devcom.modules.missions.tech.application.idempotency import (
    payload_hash,
    resolve_idempotency,
)
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.application.pipeline_builder import build_pipeline_results
from devcom.modules.missions.tech.domain.blocking import BlockingPolicy
from devcom.modules.missions.tech.domain.errors import TechNotFoundError, TechValidationError
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import IDEM_RUN, TechReviewStatus
from devcom.modules.missions.tech.ports.idempotency_store import IdempotencyStore
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class RunTechPipelineCommand:
    review_id: str
    idempotency_key: str


class RunTechPipeline:
    def __init__(
        self,
        repository: TechReviewRepository,
        catalog: ScenarioCatalog,
        registry: CapabilityRegistry,
        policy: PermissionPolicy,
        blocking: BlockingPolicy,
        idempotency: IdempotencyStore,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._catalog = catalog
        self._registry = registry
        self._policy = policy
        self._blocking = blocking
        self._idempotency = idempotency
        self._clock = clock

    def execute(self, command: RunTechPipelineCommand) -> TechReview:
        require_tech_action(self._policy, "tech.review.run")
        if not command.idempotency_key.strip():
            raise TechValidationError("idempotency key is required")
        digest = payload_hash({"review_id": command.review_id})
        existing_id = resolve_idempotency(
            self._idempotency,
            operation=IDEM_RUN,
            key=command.idempotency_key,
            expected_hash=digest,
        )
        if existing_id is not None:
            return self._require(existing_id)
        return self._run(command, digest)

    def _run(self, command: RunTechPipelineCommand, digest: str) -> TechReview:
        review = self._require(command.review_id)
        if review.status in {
            TechReviewStatus.AWAITING_DECISION,
            TechReviewStatus.DECIDED,
        }:
            return review
        if review.scenario_id is None:
            raise TechValidationError("scenario must be selected before run")
        payload = self._catalog.load_payload(review.scenario_id)
        analyses, challenges, synthesis, proposals = build_pipeline_results(
            payload,
            self._registry,
            self._blocking,
        )
        review.apply_pipeline_results(
            analyses=analyses,
            challenges=challenges,
            synthesis=synthesis,
            proposals=proposals,
            contract_versions=(
                self._registry.version,
                self._policy.version,
                self._blocking.version,
            ),
            now=self._clock.now(),
        )
        self._repository.save_atomic(
            review,
            idem_operation=IDEM_RUN,
            idem_key=command.idempotency_key,
            idem_hash=digest,
        )
        return review

    def _require(self, review_id: str) -> TechReview:
        review = self._repository.get_by_id(review_id)
        if review is None:
            raise TechNotFoundError(f"tech review {review_id} not found")
        return review
