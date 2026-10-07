from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FindingDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    domain: str
    observation: str
    evidence_refs: list[str]
    risk_level: str
    recommendation: str
    hypotheses: list[str]


class SpecialistAnalysisDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str
    capability_id: str
    findings: list[FindingDto]
    unknowns: list[str]
    out_of_scope_findings: list[str]


class ChallengeDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    challenger_agent_id: str
    target_finding_id: str
    objection: str
    evidence_refs: list[str]
    author_response: str
    domain: str


class DisagreementDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    summary: str
    related_finding_ids: list[str]
    related_challenge_ids: list[str]


class SynthesisDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    disagreements: list[DisagreementDto]
    evidence_refs: list[str]


class ProposalDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    solution: str
    advantages: list[str]
    risks: list[str]
    tradeoffs: list[str]
    validations: list[str]
    effort: str
    related_finding_ids: list[str]
    accepts_finding_ids: list[str]
    blocked: bool
    block_reason: str | None
    lift_conditions: list[str]


class SnapshotDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str
    project_name: str
    project_description: str
    project_updated_at: str
    captured_at: str


class DecisionDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    proposal_version: int
    rationale: str
    author: str
    decided_at: str


class AdrDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    body: str
    demo_warning: str


class PipelineStepDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_key: str
    phase: str
    agent_id: str
    status: str
    optional: bool
    error_message: str | None
    cost_status: str | None


class UsageRecordDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_key: str
    provider: str
    model_id: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    usd_micros: int
    eur_micros: int
    cost_status: str
    result_status: str
    created_at: str


class TechReviewDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    project_id: str
    request_text: str
    status: str
    created_at: datetime
    updated_at: datetime
    disclaimer: str
    unmatched_request: bool
    suggested_scenario_id: str | None
    scenario_id: str | None
    scenario_version: int | None
    scenario_label_note: str | None
    snapshot: SnapshotDto | None
    analyses: list[SpecialistAnalysisDto]
    challenges: list[ChallengeDto]
    synthesis: SynthesisDto | None
    proposals: list[ProposalDto]
    proposals_version: int
    decision: DecisionDto | None
    adr: AdrDto | None
    capability_registry_version: int | None
    permission_policy_version: int | None
    blocking_policy_version: int | None
    execution_mode: str = "demo"
    envelope_usd_micros: int | None = None
    envelope_eur_micros: int | None = None
    failure_message: str | None = None
    frozen_plan: dict[str, Any] | None = None
    steps: list[PipelineStepDto] = Field(default_factory=list)
    usage: list[UsageRecordDto] = Field(default_factory=list)
    reservation_status: str | None = None


class TechReviewListDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[TechReviewDto]


class ScenarioDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str


class ScenarioListDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ScenarioDto]
    disclaimer: str


class CreateTechReviewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=36)
    request_text: str = Field(min_length=1, max_length=2000)
    idempotency_key: str = Field(min_length=1, max_length=128)
    execution_mode: str = Field(default="demo", pattern="^(demo|real)$")


class SelectScenarioBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=128)


class RunTechPipelineBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=1, max_length=128)


class DecideTechReviewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str = Field(min_length=1, max_length=64)
    proposal_version: int = Field(ge=1)
    rationale: str = Field(min_length=1, max_length=2000)
    idempotency_key: str = Field(min_length=1, max_length=128)


class BudgetSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    month_id: str
    cap_eur_micros: int
    confirmed_eur_micros: int
    reserved_eur_micros: int
    uncertain_eur_micros: int
