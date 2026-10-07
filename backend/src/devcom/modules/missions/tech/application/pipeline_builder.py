from __future__ import annotations

from typing import Any

from devcom.modules.missions.domain.assignment_guard import assign_agent
from devcom.modules.missions.domain.capability import CapabilityRegistry
from devcom.modules.missions.domain.errors import OutOfScopeAssignmentError
from devcom.modules.missions.tech.domain.artifacts import (
    Challenge,
    Disagreement,
    Finding,
    Proposal,
    SpecialistAnalysis,
    Synthesis,
)
from devcom.modules.missions.tech.domain.blocking import BlockingPolicy, apply_blocking_policy
from devcom.modules.missions.tech.domain.errors import ScenarioContractError
from devcom.modules.missions.tech.domain.scenario_validator import validate_scenario_contract
from devcom.modules.missions.tech.domain.status import EffortBand, RiskLevel


def build_pipeline_results(
    payload: dict[str, Any],
    registry: CapabilityRegistry,
    blocking_policy: BlockingPolicy,
) -> tuple[list[SpecialistAnalysis], list[Challenge], Synthesis, list[Proposal]]:
    validate_scenario_contract(payload, registry)
    analyses, findings = _build_analyses(payload, registry)
    challenges = [_challenge(raw) for raw in payload.get("challenges", [])]
    synthesis = _build_synthesis(payload, analyses)
    _require_synthesizer(registry)
    open_proposals = [_proposal(raw) for raw in payload["proposals"]]
    proposals = apply_blocking_policy(blocking_policy, findings, open_proposals)
    return analyses, challenges, synthesis, proposals


def _build_analyses(
    payload: dict[str, Any],
    registry: CapabilityRegistry,
) -> tuple[list[SpecialistAnalysis], dict[str, Finding]]:
    analyses: list[SpecialistAnalysis] = []
    findings: dict[str, Finding] = {}
    for item in payload["specialists"]:
        assign_agent(registry, item["capability_id"], item["agent_id"], "pipeline")
        parsed = tuple(_finding(raw) for raw in item["findings"])
        for finding in parsed:
            findings[finding.id] = finding
        analyses.append(
            SpecialistAnalysis(
                agent_id=item["agent_id"],
                capability_id=item["capability_id"],
                findings=parsed,
                unknowns=tuple(item.get("unknowns", [])),
                out_of_scope_findings=tuple(item.get("out_of_scope_findings", [])),
            )
        )
    return analyses, findings


def _build_synthesis(
    payload: dict[str, Any],
    analyses: list[SpecialistAnalysis],
) -> Synthesis:
    disagreements = tuple(
        Disagreement(
            id=raw["id"],
            summary=raw["summary"],
            related_finding_ids=tuple(raw.get("related_finding_ids", [])),
            related_challenge_ids=tuple(raw.get("related_challenge_ids", [])),
        )
        for raw in payload.get("disagreements", [])
    )
    evidence = tuple(
        ref
        for analysis in analyses
        for finding in analysis.findings
        for ref in finding.evidence_refs
    )
    return Synthesis(
        summary=(
            "Synthèse déterministe des conclusions spécialisées ; "
            "aucune expertise inventée par le Synthétiseur."
        ),
        disagreements=disagreements,
        evidence_refs=evidence,
    )


def _require_synthesizer(registry: CapabilityRegistry) -> None:
    try:
        assign_agent(registry, "tech.synthesize", "synthetiseur_tech", "pipeline")
    except OutOfScopeAssignmentError as exc:
        raise ScenarioContractError(str(exc)) from exc


def _finding(raw: dict[str, Any]) -> Finding:
    return Finding(
        id=raw["id"],
        domain=raw["domain"],
        observation=raw["observation"],
        evidence_refs=tuple(raw.get("evidence_refs", [])),
        risk_level=RiskLevel(raw["risk_level"]),
        recommendation=raw["recommendation"],
        hypotheses=tuple(raw.get("hypotheses", [])),
    )


def _challenge(raw: dict[str, Any]) -> Challenge:
    return Challenge(
        id=raw["id"],
        challenger_agent_id=raw["challenger_agent_id"],
        target_finding_id=raw["target_finding_id"],
        objection=raw["objection"],
        evidence_refs=tuple(raw.get("evidence_refs", [])),
        author_response=raw["author_response"],
        domain=raw["domain"],
    )


def _proposal(raw: dict[str, Any]) -> Proposal:
    return Proposal(
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
