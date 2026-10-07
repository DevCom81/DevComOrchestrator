from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from devcom.entrypoints.http.deps import ContainerDep
from devcom.entrypoints.http.routers.tech_reviews import _present
from devcom.entrypoints.http.schemas.tech_event_schemas import (
    AcknowledgeUncertaintyBody,
    TechEventDto,
    TechEventListDto,
)
from devcom.entrypoints.http.schemas.tech_schemas import TechReviewDto
from devcom.modules.missions.tech.application.acknowledge_uncertainty import (
    AcknowledgeUncertaintyCommand,
)
from devcom.modules.missions.tech.application.get_review import GetTechReviewQuery
from devcom.modules.missions.tech.application.list_events import ListTechEventsQuery
from devcom.modules.missions.tech.domain.status import TechReviewStatus

router = APIRouter(tags=["tech-events"])

SSE_IDLE_ROUNDS = 30
SSE_SLEEP_SEC = 1.0
SSE_PAGE = 50
TERMINAL = {
    TechReviewStatus.AWAITING_DECISION,
    TechReviewStatus.DECIDED,
    TechReviewStatus.FAILED_PARTIAL,
    TechReviewStatus.INTERRUPTED,
    TechReviewStatus.BLOCKED_UNCERTAIN,
    TechReviewStatus.PAUSED_BUDGET,
}


@router.get("/api/tech/reviews/{review_id}/events", response_model=TechEventListDto)
def list_events(
    review_id: str,
    container: ContainerDep,
    after_seq: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> TechEventListDto:
    raw = container.list_tech_events.execute(
        ListTechEventsQuery(review_id=review_id, after_seq=after_seq, limit=limit)
    )
    return TechEventListDto(
        review_id=str(raw["review_id"]),
        after_seq=int(raw["after_seq"]),
        latest_seq=int(raw["latest_seq"]),
        items=[TechEventDto(**item) for item in raw["items"]],
    )


@router.get("/api/tech/reviews/{review_id}/events/stream")
async def stream_events(
    review_id: str,
    request: Request,
    container: ContainerDep,
    after_seq: int = Query(default=0, ge=0),
) -> StreamingResponse:
    return StreamingResponse(
        _sse(review_id, after_seq, request, container),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/api/tech/reviews/{review_id}/acknowledge-uncertainty",
    response_model=TechReviewDto,
)
def acknowledge_uncertainty(
    review_id: str,
    body: AcknowledgeUncertaintyBody,
    container: ContainerDep,
) -> TechReviewDto:
    review = container.acknowledge_uncertainty.execute(
        AcknowledgeUncertaintyCommand(
            review_id=review_id,
            reason=body.reason,
            idempotency_key=body.idempotency_key,
        )
    )
    return _present(container, review)


async def _sse(
    review_id: str,
    after_seq: int,
    request: Request,
    container: ContainerDep,
) -> AsyncIterator[str]:
    cursor = after_seq
    idle = 0
    while idle < SSE_IDLE_ROUNDS:
        if await request.is_disconnected():
            break
        page = container.list_tech_events.execute(
            ListTechEventsQuery(review_id=review_id, after_seq=cursor, limit=SSE_PAGE)
        )
        items = list(page["items"])
        if items:
            idle = 0
            for item in items:
                cursor = int(item["seq"])
                yield f"id: {cursor}\ndata: {json.dumps(item, ensure_ascii=False)}\n\n"
        else:
            idle += 1
            yield ": keepalive\n\n"
            await asyncio.sleep(SSE_SLEEP_SEC)
        review = container.get_tech_review.execute(GetTechReviewQuery(review_id=review_id))
        if review.status in TERMINAL and not items:
            break
