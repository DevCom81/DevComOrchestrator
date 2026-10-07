from __future__ import annotations

from datetime import UTC
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from devcom.modules.missions.tech.adapters import review_codec as codec
from devcom.modules.missions.tech.adapters.sqlalchemy_models import (
    TechAdrRow,
    TechDecisionRow,
    TechReviewRow,
)
from devcom.modules.missions.tech.domain.artifacts import (
    ArchitectureDecisionRecord,
    Decision,
)
from devcom.modules.missions.tech.domain.errors import TechConflictError
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import ExecutionMode, TechReviewStatus


def to_row(review: TechReview) -> TechReviewRow:
    snapshot = None if review.snapshot is None else codec.dumps(
        codec.snapshot_to_dict(review.snapshot)
    )
    return TechReviewRow(
        id=review.id,
        project_id=review.project_id,
        request_text=review.request_text,
        status=review.status.value,
        created_at=review.created_at,
        updated_at=review.updated_at,
        disclaimer=review.disclaimer,
        unmatched_request=1 if review.unmatched_request else 0,
        scenario_id=review.scenario_id,
        scenario_version=review.scenario_version,
        scenario_label_note=review.scenario_label_note,
        snapshot_json=snapshot,
        analyses_json=codec.analyses_to_json(review.analyses),
        challenges_json=codec.challenges_to_json(review.challenges),
        synthesis_json=codec.synthesis_to_json(review.synthesis),
        proposals_json=codec.proposals_to_json(review.proposals),
        proposals_version=review.proposals_version,
        capability_registry_version=review.capability_registry_version,
        permission_policy_version=review.permission_policy_version,
        blocking_policy_version=review.blocking_policy_version,
        create_idempotency_key=review.create_idempotency_key,
        execution_mode=review.execution_mode.value,
        plan_json=review.plan_json,
        envelope_usd_micros=review.envelope_usd_micros,
        envelope_eur_micros=review.envelope_eur_micros,
        failure_message=review.failure_message,
        frozen_models_json=review.frozen_models_json,
    )


def copy_row(source: TechReviewRow, target: TechReviewRow) -> None:
    for field in source.__table__.columns.keys():
        if field == "id":
            continue
        setattr(target, field, getattr(source, field))


def from_row(session: Session, row: TechReviewRow) -> TechReview:
    decision, adr = _load_decision_adr(session, row.id)
    created = row.created_at if row.created_at.tzinfo else row.created_at.replace(tzinfo=UTC)
    updated = row.updated_at if row.updated_at.tzinfo else row.updated_at.replace(tzinfo=UTC)
    snapshot_data = codec.loads(row.snapshot_json)
    snapshot = None if snapshot_data is None else codec.snapshot_from_dict(snapshot_data)
    return TechReview(
        id=row.id,
        project_id=row.project_id,
        request_text=row.request_text,
        status=TechReviewStatus(row.status),
        created_at=created,
        updated_at=updated,
        disclaimer=row.disclaimer,
        unmatched_request=bool(row.unmatched_request),
        scenario_id=row.scenario_id,
        scenario_version=row.scenario_version,
        scenario_label_note=row.scenario_label_note,
        snapshot=snapshot,
        analyses=codec.analyses_from_json(row.analyses_json),
        challenges=codec.challenges_from_json(row.challenges_json),
        synthesis=codec.synthesis_from_json(row.synthesis_json),
        proposals=codec.proposals_from_json(row.proposals_json),
        proposals_version=row.proposals_version,
        decision=decision,
        adr=adr,
        capability_registry_version=row.capability_registry_version,
        permission_policy_version=row.permission_policy_version,
        blocking_policy_version=row.blocking_policy_version,
        create_idempotency_key=row.create_idempotency_key,
        execution_mode=ExecutionMode(row.execution_mode or "demo"),
        plan_json=row.plan_json,
        envelope_usd_micros=row.envelope_usd_micros,
        envelope_eur_micros=row.envelope_eur_micros,
        failure_message=row.failure_message,
        frozen_models_json=row.frozen_models_json,
    )


def _load_decision_adr(
    session: Session,
    review_id: str,
) -> tuple[Decision | None, ArchitectureDecisionRecord | None]:
    decision_row = session.scalars(
        select(TechDecisionRow).where(TechDecisionRow.review_id == review_id)
    ).first()
    adr_row = session.scalars(
        select(TechAdrRow).where(TechAdrRow.review_id == review_id)
    ).first()
    decision = None
    if decision_row is not None:
        decision = Decision(
            proposal_id=decision_row.proposal_id,
            proposal_version=decision_row.proposal_version,
            rationale=decision_row.rationale,
            author=decision_row.author,
            decided_at=decision_row.decided_at,
        )
    adr = None
    if adr_row is not None:
        adr = ArchitectureDecisionRecord(
            id=adr_row.id,
            title=adr_row.title,
            body=adr_row.body,
            demo_warning=adr_row.demo_warning,
        )
    return decision, adr


def upsert_decision(session: Session, review: TechReview) -> None:
    if review.decision is None or review.adr is None:
        return
    existing = session.scalars(
        select(TechDecisionRow).where(TechDecisionRow.review_id == review.id)
    ).first()
    if existing is not None:
        if existing.proposal_id != review.decision.proposal_id:
            raise TechConflictError("review already has a different decision")
        return
    session.add(
        TechDecisionRow(
            id=str(uuid4()),
            review_id=review.id,
            proposal_id=review.decision.proposal_id,
            proposal_version=review.decision.proposal_version,
            rationale=review.decision.rationale,
            author=review.decision.author,
            decided_at=review.decision.decided_at,
        )
    )
    session.add(
        TechAdrRow(
            id=review.adr.id,
            review_id=review.id,
            title=review.adr.title,
            body=review.adr.body,
            demo_warning=review.adr.demo_warning,
        )
    )
