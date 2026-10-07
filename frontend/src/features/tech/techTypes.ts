export type TechReviewStatus =
  | "selecting_scenario"
  | "ready_to_run"
  | "awaiting_decision"
  | "decided";

export type FindingDto = {
  id: string;
  domain: string;
  observation: string;
  evidence_refs: string[];
  risk_level: string;
  recommendation: string;
  hypotheses: string[];
};

export type SpecialistAnalysisDto = {
  agent_id: string;
  capability_id: string;
  findings: FindingDto[];
  unknowns: string[];
  out_of_scope_findings: string[];
};

export type ChallengeDto = {
  id: string;
  challenger_agent_id: string;
  target_finding_id: string;
  objection: string;
  evidence_refs: string[];
  author_response: string;
  domain: string;
};

export type DisagreementDto = {
  id: string;
  summary: string;
  related_finding_ids: string[];
  related_challenge_ids: string[];
};

export type SynthesisDto = {
  summary: string;
  disagreements: DisagreementDto[];
  evidence_refs: string[];
};

export type ProposalDto = {
  id: string;
  title: string;
  solution: string;
  advantages: string[];
  risks: string[];
  tradeoffs: string[];
  validations: string[];
  effort: string;
  related_finding_ids: string[];
  accepts_finding_ids: string[];
  blocked: boolean;
  block_reason: string | null;
  lift_conditions: string[];
};

export type SnapshotDto = {
  project_id: string;
  project_name: string;
  project_description: string;
  project_updated_at: string;
  captured_at: string;
};

export type DecisionDto = {
  proposal_id: string;
  proposal_version: number;
  rationale: string;
  author: string;
  decided_at: string;
};

export type AdrDto = {
  id: string;
  title: string;
  body: string;
  demo_warning: string;
};

export type TechReviewDto = {
  id: string;
  project_id: string;
  request_text: string;
  status: TechReviewStatus;
  created_at: string;
  updated_at: string;
  disclaimer: string;
  unmatched_request: boolean;
  suggested_scenario_id: string | null;
  scenario_id: string | null;
  scenario_version: number | null;
  scenario_label_note: string | null;
  snapshot: SnapshotDto | null;
  analyses: SpecialistAnalysisDto[];
  challenges: ChallengeDto[];
  synthesis: SynthesisDto | null;
  proposals: ProposalDto[];
  proposals_version: number;
  decision: DecisionDto | null;
  adr: AdrDto | null;
  capability_registry_version: number | null;
  permission_policy_version: number | null;
  blocking_policy_version: number | null;
};

export type TechReviewListDto = { items: TechReviewDto[] };

export type ScenarioDto = { id: string; label: string };
export type ScenarioListDto = { items: ScenarioDto[]; disclaimer: string };

export const REQUEST_MAX = 2000;
export const RATIONALE_MAX = 2000;

export function techStatusLabel(status: TechReviewStatus): string {
  switch (status) {
    case "selecting_scenario":
      return "Choix du scénario";
    case "ready_to_run":
      return "Prête à lancer";
    case "awaiting_decision":
      return "Décision requise";
    case "decided":
      return "Décidée";
    default:
      return status;
  }
}

export function newIdempotencyKey(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}
