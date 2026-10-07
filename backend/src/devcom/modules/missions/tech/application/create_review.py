from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.ports.project_existence import ProjectExistencePort
from devcom.modules.missions.tech.adapters.scenario_catalog import ScenarioCatalog
from devcom.modules.missions.tech.application.idempotency import (
    payload_hash,
    resolve_idempotency,
)
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.application.prepare_real_review import PrepareRealReview
from devcom.modules.missions.tech.domain.errors import (
    TechConflictError,
    TechNotFoundError,
    TechValidationError,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import IDEM_CREATE, ExecutionMode
from devcom.modules.missions.tech.ports.idempotency_store import IdempotencyStore
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class CreateTechReviewCommand:
    project_id: str
    request_text: str
    idempotency_key: str
    execution_mode: ExecutionMode = ExecutionMode.DEMO
    code_snapshot_id: str | None = None


class CreateTechReview:
    def __init__(
        self,
        repository: TechReviewRepository,
        projects: ProjectExistencePort,
        catalog: ScenarioCatalog,
        policy: PermissionPolicy,
        idempotency: IdempotencyStore,
        clock: Clock,
        prepare_real: PrepareRealReview | None = None,
    ) -> None:
        self._repository = repository
        self._projects = projects
        self._catalog = catalog
        self._policy = policy
        self._idempotency = idempotency
        self._clock = clock
        self._prepare_real = prepare_real

    def execute(self, command: CreateTechReviewCommand) -> TechReview:
        require_tech_action(self._policy, "tech.review.create")
        if not command.idempotency_key.strip():
            raise TechValidationError("idempotency key is required")
        if not self._projects.exists(command.project_id):
            raise TechNotFoundError(f"project {command.project_id} not found")
        digest = payload_hash(
            {
                "project_id": command.project_id,
                "request_text": command.request_text.strip(),
                "execution_mode": command.execution_mode.value,
                "code_snapshot_id": command.code_snapshot_id,
            }
        )
        existing = self._replay(command.idempotency_key, digest)
        if existing is not None:
            return existing
        return self._create_new(command, digest)

    def _replay(self, key: str, digest: str) -> TechReview | None:
        existing_id = resolve_idempotency(
            self._idempotency,
            operation=IDEM_CREATE,
            key=key,
            expected_hash=digest,
        )
        if existing_id is None:
            return None
        review = self._repository.get_by_id(existing_id)
        if review is None:
            raise TechNotFoundError("idempotent review missing")
        return review

    def _create_new(self, command: CreateTechReviewCommand, digest: str) -> TechReview:
        if command.execution_mode == ExecutionMode.REAL:
            return self._create_real(command, digest)
        unmatched = self._catalog.match(command.request_text) is None
        review = TechReview.create(
            project_id=command.project_id,
            request_text=command.request_text,
            disclaimer=self._catalog.disclaimer,
            now=self._clock.now(),
            unmatched=unmatched,
            create_key=command.idempotency_key,
            execution_mode=ExecutionMode.DEMO,
        )
        return self._persist(review, command.idempotency_key, digest)

    def _create_real(self, command: CreateTechReviewCommand, digest: str) -> TechReview:
        if self._prepare_real is None:
            raise TechValidationError("real review preparation is not configured")
        review = TechReview.create(
            project_id=command.project_id,
            request_text=command.request_text,
            disclaimer=self._catalog.disclaimer,
            now=self._clock.now(),
            unmatched=False,
            create_key=command.idempotency_key,
            execution_mode=ExecutionMode.REAL,
            code_snapshot_id=command.code_snapshot_id,
        )
        self._prepare_real.apply(review)
        return self._persist(review, command.idempotency_key, digest)

    def _persist(self, review: TechReview, key: str, digest: str) -> TechReview:
        try:
            self._repository.save_atomic(
                review,
                idem_operation=IDEM_CREATE,
                idem_key=key,
                idem_hash=digest,
            )
        except TechConflictError:
            replayed = self._replay(key, digest)
            if replayed is None:
                raise
            return replayed
        return review
