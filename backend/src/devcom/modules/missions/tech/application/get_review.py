from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.tech.domain.errors import TechNotFoundError
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository


@dataclass(frozen=True, slots=True)
class GetTechReviewQuery:
    review_id: str


class GetTechReview:
    def __init__(self, repository: TechReviewRepository) -> None:
        self._repository = repository

    def execute(self, query: GetTechReviewQuery) -> TechReview:
        review = self._repository.get_by_id(query.review_id)
        if review is None:
            raise TechNotFoundError(f"tech review {query.review_id} not found")
        return review
