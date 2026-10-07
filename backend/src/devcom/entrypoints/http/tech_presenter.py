from __future__ import annotations

import json
from typing import Any

from devcom.entrypoints.http.code_sources_presenter import code_sources_dto
from devcom.entrypoints.http.schemas.tech_schemas import (
    AdrDto,
    ChallengeDto,
    DecisionDto,
    DisagreementDto,
    FindingDto,
    PipelineStepDto,
    ProposalDto,
    SnapshotDto,
    SpecialistAnalysisDto,
    SynthesisDto,
    TechReviewDto,
    UsageRecordDto,
)
from devcom.modules.missions.tech.adapters.scenario_catalog import ScenarioCatalog
from devcom.modules.missions.tech.application.list_scenarios import suggested_scenario_id
from devcom.modules.missions.tech.domain.artifacts import (
    Challenge,
    Finding,
    Proposal,
    SpecialistAnalysis,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.projects.domain.code_artifacts import CodeSnapshot


def review_to_dto(
    review: TechReview,
    catalog: ScenarioCatalog,
    *,
    steps: list[dict[str, Any]] | None = None,
    usage: list[dict[str, Any]] | None = None,
    reservation: dict[str, Any] | None = None,
    code_snapshot: CodeSnapshot | None = None,
) -> TechReviewDto:
    suggested = None
    if review.scenario_id is None and review.execution_mode.value == "demo":
        suggested = suggested_scenario_id(catalog, review.request_text)
    frozen = json.loads(review.frozen_models_json) if review.frozen_models_json else None
    return TechReviewDto(
        id=review.id,
        project_id=review.project_id,
        request_text=review.request_text,
        status=review.status.value,
        created_at=review.created_at,
        updated_at=review.updated_at,
        disclaimer=review.disclaimer,
        unmatched_request=review.unmatched_request,
        suggested_scenario_id=suggested,
        scenario_id=review.scenario_id,
        scenario_version=review.scenario_version,
        scenario_label_note=review.scenario_label_note,
        snapshot=_snapshot(review),
        analyses=[_analysis(item) for item in review.analyses],
        challenges=[_challenge(item) for item in review.challenges],
        synthesis=_synthesis(review),
        proposals=[_proposal(item) for item in review.proposals],
        proposals_version=review.proposals_version,
        decision=_decision(review),
        adr=_adr(review),
        capability_registry_version=review.capability_registry_version,
        permission_policy_version=review.permission_policy_version,
        blocking_policy_version=review.blocking_policy_version,
        code_snapshot_id=review.code_snapshot_id,
        code_sources=code_sources_dto(code_snapshot),
        **_real_fields(review, frozen, steps, usage, reservation),
    )


def _real_fields(
    review: TechReview,
    frozen: dict[str, Any] | None,
    steps: list[dict[str, Any]] | None,
    usage: list[dict[str, Any]] | None,
    reservation: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "execution_mode": review.execution_mode.value,
        "envelope_usd_micros": review.envelope_usd_micros,
        "envelope_eur_micros": review.envelope_eur_micros,
        "failure_message": review.failure_message,
        "frozen_plan": frozen,
        "steps": [_step(item) for item in steps or []],
        "usage": [_usage(item) for item in usage or []],
        "reservation_status": None if reservation is None else str(reservation["status"]),
        "uncertainty_ack_at": review.uncertainty_ack_at,
        "uncertainty_ack_reason": review.uncertainty_ack_reason,
    }


def _snapshot(review: TechReview) -> SnapshotDto | None:
    if review.snapshot is None:
        return None
    snap = review.snapshot
    return SnapshotDto(
        project_id=snap.project_id,
        project_name=snap.project_name,
        project_description=snap.project_description,
        project_updated_at=snap.project_updated_at,
        captured_at=snap.captured_at,
        code_snapshot_id=snap.code_snapshot_id,
        has_code_sources=snap.has_code_sources,
    )


def _analysis(item: SpecialistAnalysis) -> SpecialistAnalysisDto:
    return SpecialistAnalysisDto(
        agent_id=item.agent_id,
        capability_id=item.capability_id,
        findings=[_finding(finding) for finding in item.findings],
        unknowns=list(item.unknowns),
        out_of_scope_findings=list(item.out_of_scope_findings),
    )


def _finding(finding: Finding) -> FindingDto:
    return FindingDto(
        id=finding.id,
        domain=finding.domain,
        observation=finding.observation,
        evidence_refs=list(finding.evidence_refs),
        risk_level=finding.risk_level.value,
        recommendation=finding.recommendation,
        hypotheses=list(finding.hypotheses),
    )


def _challenge(item: Challenge) -> ChallengeDto:
    return ChallengeDto(
        id=item.id,
        challenger_agent_id=item.challenger_agent_id,
        target_finding_id=item.target_finding_id,
        objection=item.objection,
        evidence_refs=list(item.evidence_refs),
        author_response=item.author_response,
        domain=item.domain,
    )


def _synthesis(review: TechReview) -> SynthesisDto | None:
    if review.synthesis is None:
        return None
    syn = review.synthesis
    return SynthesisDto(
        summary=syn.summary,
        evidence_refs=list(syn.evidence_refs),
        disagreements=[
            DisagreementDto(
                id=item.id,
                summary=item.summary,
                related_finding_ids=list(item.related_finding_ids),
                related_challenge_ids=list(item.related_challenge_ids),
            )
            for item in syn.disagreements
        ],
    )


def _proposal(item: Proposal) -> ProposalDto:
    return ProposalDto(
        id=item.id,
        title=item.title,
        solution=item.solution,
        advantages=list(item.advantages),
        risks=list(item.risks),
        tradeoffs=list(item.tradeoffs),
        validations=list(item.validations),
        effort=item.effort.value,
        related_finding_ids=list(item.related_finding_ids),
        accepts_finding_ids=list(item.accepts_finding_ids),
        blocked=item.blocked,
        block_reason=item.block_reason,
        lift_conditions=list(item.lift_conditions),
    )


def _decision(review: TechReview) -> DecisionDto | None:
    if review.decision is None:
        return None
    decision = review.decision
    return DecisionDto(
        proposal_id=decision.proposal_id,
        proposal_version=decision.proposal_version,
        rationale=decision.rationale,
        author=decision.author,
        decided_at=decision.decided_at,
    )


def _adr(review: TechReview) -> AdrDto | None:
    if review.adr is None:
        return None
    adr = review.adr
    return AdrDto(
        id=adr.id,
        title=adr.title,
        body=adr.body,
        demo_warning=adr.demo_warning,
    )


def _step(item: dict[str, Any]) -> PipelineStepDto:
    return PipelineStepDto(
        step_key=str(item["step_key"]),
        phase=str(item["phase"]),
        agent_id=str(item["agent_id"]),
        status=str(item["status"]),
        optional=bool(item["optional"]),
        error_message=item.get("error_message"),
        cost_status=item.get("cost_status"),
    )


def _usage(item: dict[str, Any]) -> UsageRecordDto:
    return UsageRecordDto(
        step_key=str(item["step_key"]),
        provider=str(item["provider"]),
        model_id=str(item["model_id"]),
        input_tokens=int(item["input_tokens"]),
        output_tokens=int(item["output_tokens"]),
        reasoning_tokens=int(item["reasoning_tokens"]),
        usd_micros=int(item["usd_micros"]),
        eur_micros=int(item["eur_micros"]),
        cost_status=str(item["cost_status"]),
        result_status=str(item["result_status"]),
        created_at=str(item["created_at"]),
    )
