from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from devcom.modules.missions.tech.domain.artifacts import (
    ArchitectureDecisionRecord,
    Challenge,
    ContextSnapshot,
    Decision,
    Proposal,
    SpecialistAnalysis,
    Synthesis,
)
from devcom.modules.missions.tech.domain.errors import (
    ProposalBlockedError,
    StaleProposalVersionError,
    TechConflictError,
    TechValidationError,
)
from devcom.modules.missions.tech.domain.status import (
    DEMO_DECISION_AUTHOR,
    RATIONALE_MAX,
    RATIONALE_MIN,
    REQUEST_MAX,
    REQUEST_MIN,
    ExecutionMode,
    TechReviewStatus,
)


@dataclass(slots=True)
class TechReview:
    id: str
    project_id: str
    request_text: str
    status: TechReviewStatus
    created_at: datetime
    updated_at: datetime
    disclaimer: str
    unmatched_request: bool = False
    scenario_id: str | None = None
    scenario_version: int | None = None
    scenario_label_note: str | None = None
    snapshot: ContextSnapshot | None = None
    analyses: list[SpecialistAnalysis] = field(default_factory=list)
    challenges: list[Challenge] = field(default_factory=list)
    synthesis: Synthesis | None = None
    proposals: list[Proposal] = field(default_factory=list)
    proposals_version: int = 0
    decision: Decision | None = None
    adr: ArchitectureDecisionRecord | None = None
    capability_registry_version: int | None = None
    permission_policy_version: int | None = None
    blocking_policy_version: int | None = None
    create_idempotency_key: str | None = None
    execution_mode: ExecutionMode = ExecutionMode.DEMO
    plan_json: str | None = None
    envelope_usd_micros: int | None = None
    envelope_eur_micros: int | None = None
    failure_message: str | None = None
    frozen_models_json: str | None = None
    code_snapshot_id: str | None = None
    uncertainty_ack_at: datetime | None = None
    uncertainty_ack_reason: str | None = None

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        request_text: str,
        disclaimer: str,
        now: datetime,
        unmatched: bool,
        create_key: str,
        execution_mode: ExecutionMode = ExecutionMode.DEMO,
        code_snapshot_id: str | None = None,
    ) -> TechReview:
        text = _bounded(request_text, REQUEST_MIN, REQUEST_MAX, "request")
        stamp = _utc(now)
        initial = (
            TechReviewStatus.SELECTING_SCENARIO
            if execution_mode == ExecutionMode.DEMO
            else TechReviewStatus.READY_TO_RUN
        )
        return cls(
            id=str(uuid4()),
            project_id=project_id,
            request_text=text,
            status=initial,
            created_at=stamp,
            updated_at=stamp,
            disclaimer=disclaimer,
            unmatched_request=unmatched,
            create_idempotency_key=create_key,
            execution_mode=execution_mode,
            code_snapshot_id=code_snapshot_id,
        )

    def confirm_scenario(
        self,
        *,
        scenario_id: str,
        scenario_version: int,
        snapshot: ContextSnapshot,
        note: str | None,
        now: datetime,
    ) -> None:
        if self.execution_mode != ExecutionMode.DEMO:
            raise TechConflictError("scenario selection is demo-only")
        if self.status not in {
            TechReviewStatus.SELECTING_SCENARIO,
            TechReviewStatus.READY_TO_RUN,
        }:
            raise TechConflictError("scenario can no longer be changed")
        if self.status == TechReviewStatus.READY_TO_RUN and self.scenario_id != scenario_id:
            raise TechConflictError("scenario already confirmed")
        self.scenario_id = scenario_id
        self.scenario_version = scenario_version
        self.snapshot = snapshot
        self.scenario_label_note = note
        self.status = TechReviewStatus.READY_TO_RUN
        self.updated_at = _utc(now)

    def mark_running(self, now: datetime) -> None:
        if self.status == TechReviewStatus.RUNNING:
            return
        if self.status != TechReviewStatus.READY_TO_RUN:
            raise TechConflictError("review is not ready to run")
        if self.snapshot is None:
            raise TechConflictError("snapshot missing")
        self.status = TechReviewStatus.RUNNING
        self.updated_at = _utc(now)

    def apply_pipeline_results(
        self,
        *,
        analyses: list[SpecialistAnalysis],
        challenges: list[Challenge],
        synthesis: Synthesis,
        proposals: list[Proposal],
        contract_versions: tuple[int, int, int],
        now: datetime,
    ) -> None:
        if self.status == TechReviewStatus.AWAITING_DECISION:
            return
        if self.status == TechReviewStatus.DECIDED:
            raise TechConflictError("review already decided")
        allowed = {TechReviewStatus.READY_TO_RUN, TechReviewStatus.RUNNING}
        if self.status not in allowed:
            raise TechConflictError("review is not ready to run")
        if self.snapshot is None:
            raise TechConflictError("snapshot missing")
        if self.execution_mode == ExecutionMode.DEMO and self.scenario_id is None:
            raise TechConflictError("scenario snapshot missing")
        self.analyses = list(analyses)
        self.challenges = list(challenges)
        self.synthesis = synthesis
        self.proposals = list(proposals)
        self.proposals_version = 1
        self.capability_registry_version = contract_versions[0]
        self.permission_policy_version = contract_versions[1]
        self.blocking_policy_version = contract_versions[2]
        self.status = TechReviewStatus.AWAITING_DECISION
        self.updated_at = _utc(now)

    def decide(
        self,
        *,
        proposal_id: str,
        proposal_version: int,
        rationale: str,
        now: datetime,
        adr_body: str,
    ) -> None:
        if self.status == TechReviewStatus.DECIDED:
            if self.decision and self.decision.proposal_id == proposal_id:
                return
            raise TechConflictError("review already has a different decision")
        if self.status != TechReviewStatus.AWAITING_DECISION:
            raise TechConflictError("review is not awaiting decision")
        if proposal_version != self.proposals_version:
            raise StaleProposalVersionError("proposal version is obsolete")
        proposal = self._find_proposal(proposal_id)
        if proposal.blocked:
            raise ProposalBlockedError(proposal.block_reason or "proposal blocked")
        text = _bounded(rationale, RATIONALE_MIN, RATIONALE_MAX, "rationale")
        stamp = _utc(now)
        self.decision = Decision(
            proposal_id=proposal_id,
            proposal_version=proposal_version,
            rationale=text,
            author=DEMO_DECISION_AUTHOR,
            decided_at=stamp.isoformat(),
        )
        self.adr = ArchitectureDecisionRecord(
            id=str(uuid4()),
            title=f"ADR — {proposal.title}",
            body=adr_body,
            demo_warning=(
                "ADR de démonstration — n'autorise aucune implémentation, "
                "modification de dépôt ni action externe."
            ),
        )
        self.status = TechReviewStatus.DECIDED
        self.updated_at = stamp

    def acknowledge_uncertainty(self, *, reason: str, now: datetime) -> None:
        if self.status != TechReviewStatus.BLOCKED_UNCERTAIN:
            raise TechConflictError("only blocked_uncertain reviews can be acknowledged")
        if self.uncertainty_ack_at is not None:
            return
        text = _bounded(reason, 1, 500, "reason")
        stamp = _utc(now)
        self.uncertainty_ack_at = stamp
        self.uncertainty_ack_reason = text
        self.updated_at = stamp

    def _find_proposal(self, proposal_id: str) -> Proposal:
        for proposal in self.proposals:
            if proposal.id == proposal_id:
                return proposal
        raise TechValidationError(f"unknown proposal `{proposal_id}`")


def _bounded(raw: str, minimum: int, maximum: int, label: str) -> str:
    text = raw.strip()
    if not (minimum <= len(text) <= maximum):
        raise TechValidationError(
            f"{label} must be {minimum} to {maximum} characters after trim"
        )
    return text


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise TechValidationError("timestamps must be timezone-aware UTC")
    return value.astimezone(UTC)
