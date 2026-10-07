from __future__ import annotations

from typing import Protocol

from devcom.modules.missions.tech.domain.review import TechReview


class TechReviewRepository(Protocol):
    def save_atomic(
        self,
        review: TechReview,
        *,
        idem_operation: str | None = None,
        idem_key: str | None = None,
        idem_hash: str | None = None,
    ) -> None:
        """Persist review and optional idempotency record atomically."""

    def get_by_id(self, review_id: str) -> TechReview | None:
        """Load one review."""

    def list_all(self) -> list[TechReview]:
        """List reviews newest first."""

    def get_by_create_key(self, key: str) -> TechReview | None:
        """Lookup by create idempotency key."""
