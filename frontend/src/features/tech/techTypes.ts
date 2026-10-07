export type TechReviewStatus =
  | "selecting_scenario"
  | "ready_to_run"
  | "running"
  | "awaiting_decision"
  | "failed_partial"
  | "interrupted"
  | "blocked_uncertain"
  | "paused_budget"
  | "decided";

export type TechEventDto = {
  id: string;
  review_id: string;
  seq: number;
  event_type: string;
  occurred_at: string;
  payload: Record<string, unknown>;
};

export type TechEventListDto = {
  review_id: string;
  after_seq: number;
  latest_seq: number;
  items: TechEventDto[];
};

export type ExecutionMode = "demo" | "real";

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
  code_snapshot_id: string | null;
  has_code_sources: boolean;
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

export type PipelineStepDto = {
  step_key: string;
  phase: string;
  agent_id: string;
  status: string;
  optional: boolean;
  error_message: string | null;
  cost_status: string | null;
};

export type UsageRecordDto = {
  step_key: string;
  provider: string;
  model_id: string;
  input_tokens: number;
  output_tokens: number;
  reasoning_tokens: number;
  usd_micros: number;
  eur_micros: number;
  cost_status: string;
  result_status: string;
  created_at: string;
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
  execution_mode: ExecutionMode;
  envelope_usd_micros: number | null;
  envelope_eur_micros: number | null;
  failure_message: string | null;
  frozen_plan: Record<string, unknown> | null;
  steps: PipelineStepDto[];
  usage: UsageRecordDto[];
  reservation_status: string | null;
  code_snapshot_id: string | null;
  code_sources: CodeSourcesDto | null;
  uncertainty_ack_at: string | null;
  uncertainty_ack_reason: string | null;
};

export type CodeSourceFileDto = {
  relative_path: string;
  sha256: string;
  byte_size: number;
  evidence_ref: string;
};

export type CodeSourcesDto = {
  has_code_sources: boolean;
  notice: string;
  snapshot_id: string | null;
  fingerprint: string | null;
  captured_at: string | null;
  git_commit: string | null;
  git_dirty: boolean | null;
  git_note: string | null;
  files: CodeSourceFileDto[];
};

export type TechReviewListDto = { items: TechReviewDto[] };

export type ScenarioDto = { id: string; label: string };
export type ScenarioListDto = { items: ScenarioDto[]; disclaimer: string };

export const REQUEST_MAX = 2000;
export const RATIONALE_MAX = 2000;

/** Spécialistes attendus d'une revue TECH (ordre d'affichage). */
export const TECH_SPECIALIST_IDS = [
  "architecte",
  "cyber",
  "qa",
  "devops",
  "fullstack",
  "sql_data",
] as const;

export function techStatusLabel(status: TechReviewStatus): string {
  switch (status) {
    case "selecting_scenario":
      return "Choix du scénario";
    case "ready_to_run":
      return "Prête à lancer";
    case "running":
      return "En cours";
    case "awaiting_decision":
      return "Décision requise";
    case "failed_partial":
      return "Échec partiel";
    case "interrupted":
      return "Interrompue";
    case "blocked_uncertain":
      return "Bloquée (incertain)";
    case "paused_budget":
      return "Pause budget";
    case "decided":
      return "Décidée";
    default:
      return status;
  }
}

export function formatEurMicros(micros: number): string {
  return `${(micros / 1_000_000).toFixed(6)} €`;
}

export function newIdempotencyKey(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}
