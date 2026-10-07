from __future__ import annotations

import hashlib
import json
from typing import Any

from devcom.modules.missions.tech.domain.errors import TechIdempotencyConflictError
from devcom.modules.missions.tech.ports.idempotency_store import IdempotencyStore


def payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def resolve_idempotency(
    store: IdempotencyStore,
    *,
    operation: str,
    key: str,
    expected_hash: str,
) -> str | None:
    existing = store.get(operation, key)
    if existing is None:
        return None
    stored_hash, resource_id = existing
    if stored_hash != expected_hash:
        raise TechIdempotencyConflictError(
            f"idempotency key reused with different payload for `{operation}`"
        )
    return resource_id
