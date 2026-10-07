from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.tech.adapters.scenario_catalog import ScenarioCatalog
from devcom.modules.missions.tech.domain.errors import TechNotFoundError, TechValidationError
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import UNMATCHED_SCENARIO_NOTE
from devcom.modules.missions.tech.ports.project_snapshot import ProjectSnapshotPort
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class SelectScenarioCommand:
    review_id: str
    scenario_id: str


class SelectScenario:
    def __init__(
        self,
        repository: TechReviewRepository,
        catalog: ScenarioCatalog,
        snapshots: ProjectSnapshotPort,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._catalog = catalog
        self._snapshots = snapshots
        self._clock = clock

    def execute(self, command: SelectScenarioCommand) -> TechReview:
        review = self._repository.get_by_id(command.review_id)
        if review is None:
            raise TechNotFoundError(f"tech review {command.review_id} not found")
        try:
            meta = self._catalog.get(command.scenario_id)
            payload = self._catalog.load_payload(command.scenario_id)
        except KeyError as exc:
            raise TechValidationError(f"unknown scenario `{command.scenario_id}`") from exc
        now = self._clock.now()
        note = UNMATCHED_SCENARIO_NOTE if review.unmatched_request else None
        if review.snapshot is None:
            snapshot = self._snapshots.capture(review.project_id, now.isoformat())
        else:
            snapshot = review.snapshot
        review.confirm_scenario(
            scenario_id=meta.id,
            scenario_version=int(payload["version"]),
            snapshot=snapshot,
            note=note,
            now=now,
        )
        self._repository.save_atomic(review)
        return review
