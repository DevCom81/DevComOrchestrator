from __future__ import annotations

from datetime import datetime
from typing import Any

from devcom.modules.missions.tech.domain.artifacts import (
    Challenge,
    Disagreement,
    Finding,
    Proposal,
    SpecialistAnalysis,
    Synthesis,
)
from devcom.modules.missions.tech.domain.blocking import BlockingPolicy, apply_blocking_policy
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import EffortBand, TechReviewStatus
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository


def finalize_real_review(
    *,
    review: TechReview,
    repository: TechReviewRepository,
    blocking: BlockingPolicy,
    analyses: dict[str, SpecialistAnalysis],
    challenges: list[Challenge],
    findings: dict[str, Finding],
    synth_result: dict[str, Any],
    registry_version: int,
    policy_version: int,
    now: datetime,
) -> None:
    synthesis = _synthesis(synth_result, findings)
    open_proposals = _proposals(synth_result)
    if not _refs_valid(open_proposals, findings):
        review.status = TechReviewStatus.FAILED_PARTIAL
        review.failure_message = "proposal references unknown finding"
        review.updated_at = now
        repository.save_atomic(review)
        return
    proposals = apply_blocking_policy(blocking, findings, open_proposals)
    review.apply_pipeline_results(
        analyses=list(analyses.values()),
        challenges=challenges,
        synthesis=synthesis,
        proposals=proposals,
        contract_versions=(registry_version, policy_version, blocking.version),
        now=now,
    )
    review.failure_message = None
    repository.save_atomic(review)


def _synthesis(parsed: dict[str, Any], findings: dict[str, Finding]) -> Synthesis:
    return Synthesis(
        summary=parsed["summary"],
        disagreements=tuple(
            Disagreement(
                id=item["id"],
                summary=item["summary"],
                related_finding_ids=tuple(item.get("related_finding_ids", [])),
                related_challenge_ids=tuple(item.get("related_challenge_ids", [])),
            )
            for item in parsed.get("disagreements", [])
        ),
        evidence_refs=tuple(
            ref for finding in findings.values() for ref in finding.evidence_refs
        ),
    )


def _proposals(parsed: dict[str, Any]) -> list[Proposal]:
    return [
        Proposal(
            id=raw["id"],
            title=raw["title"],
            solution=raw["solution"],
            advantages=tuple(raw.get("advantages", [])),
            risks=tuple(raw.get("risks", [])),
            tradeoffs=tuple(raw.get("tradeoffs", [])),
            validations=tuple(raw.get("validations", [])),
            effort=EffortBand(raw["effort"]),
            related_finding_ids=tuple(raw.get("related_finding_ids", [])),
            accepts_finding_ids=tuple(raw.get("accepts_finding_ids", [])),
            blocked=False,
            block_reason=None,
            lift_conditions=(),
        )
        for raw in parsed["proposals"]
    ]


def _refs_valid(proposals: list[Proposal], findings: dict[str, Finding]) -> bool:
    for proposal in proposals:
        for finding_id in proposal.related_finding_ids + proposal.accepts_finding_ids:
            if finding_id not in findings:
                return False
    return True
