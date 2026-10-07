from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from devcom.modules.missions.tech.adapters.sqlalchemy_events import SqlAlchemyEventStore
from devcom.modules.missions.tech.domain.errors import TechNotFoundError
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository


@dataclass(frozen=True, slots=True)
class ListTechEventsQuery:
    review_id: str
    after_seq: int = 0
    limit: int = 50


class ListTechEvents:
    def __init__(
        self,
        repository: TechReviewRepository,
        events: SqlAlchemyEventStore,
    ) -> None:
        self._repository = repository
        self._events = events

    def execute(self, query: ListTechEventsQuery) -> dict[str, Any]:
        review = self._repository.get_by_id(query.review_id)
        if review is None:
            raise TechNotFoundError(f"tech review {query.review_id} not found")
        after = max(0, query.after_seq)
        items = self._events.list_after(query.review_id, after, query.limit)
        return {
            "review_id": query.review_id,
            "after_seq": after,
            "latest_seq": self._events.latest_seq(query.review_id),
            "items": items,
        }
