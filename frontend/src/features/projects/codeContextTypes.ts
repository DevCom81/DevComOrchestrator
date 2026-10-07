export type SourceRootDto = {
  project_id: string;
  absolute_path: string;
  exclusions: string[];
  attached_at: string | null;
  mode: string;
  demo_fixture: boolean;
  note?: string | null;
};

export type TreeEntryDto = {
  relative_path: string;
  name: string;
  kind: string;
  excluded: boolean;
  exclusion_reason: string | null;
};

export type SourceTreeDto = {
  project_id: string;
  root_path: string;
  entries: TreeEntryDto[];
  cursor: string | null;
  truncated: boolean;
  limit_message: string | null;
  secret_scan_disclaimer: string;
};

export type PreviewFileDto = {
  relative_path: string;
  sha256: string;
  byte_size: number;
  content: string;
  evidence_ref: string;
};

export type CodePreviewDto = {
  preview_id: string;
  project_id: string;
  fingerprint: string;
  created_at: string;
  expires_at: string;
  files: PreviewFileDto[];
  exclusions: string[];
  token_upper_bound: number;
  token_indicative: number;
  token_method_blocking: string;
  token_method_indicative: string;
  reserves_budget: boolean;
  provider_calls: number;
};

export type CodeSnapshotDto = {
  snapshot_id: string;
  project_id: string;
  preview_id: string;
  fingerprint: string;
  captured_at: string;
  files: PreviewFileDto[];
  exclusions: string[];
  git_commit: string | null;
  git_dirty: boolean | null;
  git_note: string;
  token_upper_bound: number;
  token_method_blocking: string;
  status: string;
};
