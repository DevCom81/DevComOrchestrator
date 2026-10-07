from __future__ import annotations

from datetime import UTC, datetime

import pytest

from devcom.modules.missions.tech.domain.artifacts import (
    ContextSnapshot,
    Proposal,
    Synthesis,
)
from devcom.modules.missions.tech.domain.errors import (
    ProposalBlockedError,
    StaleProposalVersionError,
    TechConflictError,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import EffortBand, TechReviewStatus

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


def _review() -> TechReview:
    return TechReview.create(
        project_id="p1",
        request_text="Revue architecture locale SQLite",
        disclaimer="demo",
        now=NOW,
        unmatched=False,
        create_key="k1",
    )


def _open(proposal_id: str = "p-b") -> Proposal:
    return Proposal(
        id=proposal_id,
        title="Option ouverte",
        solution="Sol",
        advantages=("a",),
        risks=("r",),
        tradeoffs=("t",),
        validations=("v",),
        effort=EffortBand.M,
        related_finding_ids=(),
        accepts_finding_ids=(),
        blocked=False,
        block_reason=None,
        lift_conditions=(),
    )


def _blocked() -> Proposal:
    return Proposal(
        id="p-a",
        title="Bloquée",
        solution="Sol",
        advantages=(),
        risks=(),
        tradeoffs=(),
        validations=(),
        effort=EffortBand.S,
        related_finding_ids=(),
        accepts_finding_ids=(),
        blocked=True,
        block_reason="critical",
        lift_conditions=("lift",),
    )


def _ready(review: TechReview) -> None:
    snap = ContextSnapshot("p1", "n", "d", NOW.isoformat(), NOW.isoformat())
    review.confirm_scenario(
        scenario_id="s",
        scenario_version=1,
        snapshot=snap,
        note=None,
        now=NOW,
    )
    review.apply_pipeline_results(
        analyses=[],
        challenges=[],
        synthesis=Synthesis(summary="s", disagreements=(), evidence_refs=()),
        proposals=[_blocked(), _open()],
        contract_versions=(2, 2, 1),
        now=NOW,
    )


def test_snapshot_frozen_and_scenario_locked() -> None:
    review = _review()
    snap = ContextSnapshot("p1", "Demo", "desc", NOW.isoformat(), NOW.isoformat())
    review.confirm_scenario(
        scenario_id="local_persistence",
        scenario_version=1,
        snapshot=snap,
        note=None,
        now=NOW,
    )
    assert review.status == TechReviewStatus.READY_TO_RUN
    with pytest.raises(TechConflictError):
        review.confirm_scenario(
            scenario_id="security_critical",
            scenario_version=1,
            snapshot=snap,
            note=None,
            now=NOW,
        )


def test_decide_blocks_stale_and_conflict() -> None:
    review = _review()
    _ready(review)
    with pytest.raises(ProposalBlockedError):
        review.decide(
            proposal_id="p-a",
            proposal_version=1,
            rationale="motif",
            now=NOW,
            adr_body="body",
        )
    with pytest.raises(StaleProposalVersionError):
        review.decide(
            proposal_id="p-b",
            proposal_version=99,
            rationale="motif",
            now=NOW,
            adr_body="body",
        )
    review.decide(
        proposal_id="p-b",
        proposal_version=1,
        rationale="motif suffisant",
        now=NOW,
        adr_body="body",
    )
    assert review.status == TechReviewStatus.DECIDED
    with pytest.raises(TechConflictError):
        review.decide(
            proposal_id="p-a",
            proposal_version=1,
            rationale="autre",
            now=NOW,
            adr_body="body",
        )
