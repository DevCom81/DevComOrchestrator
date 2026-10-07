export type MissionStatus =
  | "draft"
  | "awaiting_clarification"
  | "routed"
  | "blocked_authorization";

export type TaskAssignmentDto = {
  id: string;
  capability_id: string;
  agent_id: string;
  status: string;
  rationale: string;
};

export type RoutingDto = {
  mode: string;
  disclaimer: string;
  rule_ids: string[];
  rationale: string;
  capability_registry_version: number;
  permission_policy_version: number;
  dispatch_rules_version: number;
};

export type ClarificationChoiceDto = {
  id: string;
  label: string;
  maps_to_rule: string;
};

export type ClarificationQuestionDto = {
  id: string;
  prompt: string;
  choices: ClarificationChoiceDto[];
};

export type AuthorizationBlockDto = {
  action_id: string;
  message: string;
  rationale: string;
};

export type MissionDto = {
  id: string;
  project_id: string;
  request_text: string;
  status: MissionStatus;
  created_at: string;
  updated_at: string;
  routing: RoutingDto | null;
  tasks: TaskAssignmentDto[];
  clarification_token: string | null;
  clarification_questions: ClarificationQuestionDto[];
  authorization_block: AuthorizationBlockDto | null;
};

export type MissionListDto = { items: MissionDto[] };

export type DemoExampleDto = {
  id: string;
  label: string;
  request_text: string;
};

export type DemoExampleListDto = {
  items: DemoExampleDto[];
  disclaimer: string;
};

export const REQUEST_MAX = 2000;

export function statusLabel(status: MissionStatus): string {
  switch (status) {
    case "draft":
      return "Brouillon";
    case "awaiting_clarification":
      return "Clarification requise";
    case "routed":
      return "Routée (sans exécution)";
    case "blocked_authorization":
      return "Autorisation requise";
    default:
      return status;
  }
}

export function statusClassName(status: MissionStatus): string {
  if (status === "blocked_authorization") {
    return "mission-status mission-status--blocked";
  }
  if (status === "routed") {
    return "mission-status mission-status--routed";
  }
  if (status === "awaiting_clarification") {
    return "mission-status mission-status--clarify";
  }
  return "mission-status";
}
