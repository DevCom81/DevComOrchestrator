from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TechEventDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    review_id: str
    seq: int
    event_type: str
    occurred_at: str
    payload: dict[str, Any]


class TechEventListDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: str
    after_seq: int
    latest_seq: int
    items: list[TechEventDto]


class AcknowledgeUncertaintyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=500)
    idempotency_key: str = Field(min_length=1, max_length=128)
