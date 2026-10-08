export type CursorPlanDto = {
  id: string;
  project_id: string;
  review_id: string;
  proposal_id: string;
  proposal_version: number;
  adr_id: string;
  code_snapshot_id: string | null;
  status: string;
  plan_version: number;
  objectif: string;
  perimetre: string;
  exclusions: string;
  contraintes_architecture: string;
  criteres_acceptation: string;
  validations_attendues: string;
  content_hash: string;
  canon_version: string;
  active_approval_id: string | null;
  preview_text: string;
  created_at: string;
  updated_at: string;
};

export type ApprovalDto = {
  id: string;
  action_id: string;
  target_id: string;
  payload_hash: string;
  resource_version: number;
  status: string;
  author: string;
  created_at: string;
  expires_at: string;
  decided_at: string | null;
  consumed_at: string | null;
};

export type CursorExportDto = {
  id: string;
  plan_id: string;
  plan_version: number;
  content_hash: string;
  approval_id: string;
  manifest_json: string;
  created_at: string;
  download_markdown: string;
};

export type CursorReturnDto = {
  id: string;
  plan_id: string;
  export_id: string;
  project_id: string;
  report_sha256: string;
  diff_sha256: string;
  report_bytes: number;
  diff_bytes: number;
  declared_base: string | null;
  declared_commit: string | null;
  verification_status: string;
  verification_notes: string;
  linked_review_id: string | null;
  imported_at: string;
};

export type ReturnContextDto = {
  return_id: string;
  plan_id: string;
  export_id: string;
  export_content_hash: string;
  export_plan_version: number;
  code_snapshot_id: string | null;
  report_sha256: string;
  diff_sha256: string;
  report_bytes: number;
  diff_bytes: number;
  verification_status: string;
  verification_notes: string;
  declared_base: string | null;
  declared_commit: string | null;
  report_text: string;
  diff_text: string;
  warning: string;
};
