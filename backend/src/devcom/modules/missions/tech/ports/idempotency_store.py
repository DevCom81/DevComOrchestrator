from __future__ import annotations

from typing import Protocol


class IdempotencyStore(Protocol):
    def get(self, operation: str, key: str) -> tuple[str, str] | None:
        """Return (payload_hash, resource_id) when present."""

    def put(self, operation: str, key: str, payload_hash: str, resource_id: str) -> None:
        """Store idempotency record; caller handles conflicts."""
