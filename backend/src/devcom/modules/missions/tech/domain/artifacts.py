from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.tech.domain.status import EffortBand, RiskLevel


@dataclass(frozen=True, slots=True)
class Finding:
    id: str
    domain: str
    observation: str
    evidence_refs: tuple[str, ...]
    risk_level: RiskLevel
    recommendation: str
    hypotheses: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SpecialistAnalysis:
    agent_id: str
    capability_id: str
    findings: tuple[Finding, ...]
    unknowns: tuple[str, ...]
    out_of_scope_findings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Challenge:
    id: str
    challenger_agent_id: str
    target_finding_id: str
    objection: str
    evidence_refs: tuple[str, ...]
    author_response: str
    domain: str


@dataclass(frozen=True, slots=True)
class Disagreement:
    id: str
    summary: str
    related_finding_ids: tuple[str, ...]
    related_challenge_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Proposal:
    id: str
    title: str
    solution: str
    advantages: tuple[str, ...]
    risks: tuple[str, ...]
    tradeoffs: tuple[str, ...]
    validations: tuple[str, ...]
    effort: EffortBand
    related_finding_ids: tuple[str, ...]
    accepts_finding_ids: tuple[str, ...]
    blocked: bool
    block_reason: str | None
    lift_conditions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Synthesis:
    summary: str
    disagreements: tuple[Disagreement, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    project_id: str
    project_name: str
    project_description: str
    project_updated_at: str
    captured_at: str


@dataclass(frozen=True, slots=True)
class Decision:
    proposal_id: str
    proposal_version: int
    rationale: str
    author: str
    decided_at: str


@dataclass(frozen=True, slots=True)
class ArchitectureDecisionRecord:
    id: str
    title: str
    body: str
    demo_warning: str
