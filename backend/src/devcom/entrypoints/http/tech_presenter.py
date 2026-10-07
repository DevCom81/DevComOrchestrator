from __future__ import annotations

from devcom.entrypoints.http.schemas.tech_schemas import (
    AdrDto,
    ChallengeDto,
    DecisionDto,
    DisagreementDto,
    FindingDto,
    ProposalDto,
    SnapshotDto,
    SpecialistAnalysisDto,
    SynthesisDto,
    TechReviewDto,
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


def review_to_dto(review: TechReview, catalog: ScenarioCatalog) -> TechReviewDto:
    suggested = None
    if review.scenario_id is None:
        suggested = suggested_scenario_id(catalog, review.request_text)
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
    )


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
