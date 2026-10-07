from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository


@dataclass(frozen=True, slots=True)
class ListTechReviewsQuery:
    project_id: str | None = None


class ListTechReviews:
    def __init__(self, repository: TechReviewRepository) -> None:
        self._repository = repository

    def execute(self, query: ListTechReviewsQuery) -> list[TechReview]:
        items = self._repository.list_all()
        if query.project_id is None:
            return items
        return [item for item in items if item.project_id == query.project_id]
