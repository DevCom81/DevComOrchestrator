from __future__ import annotations

import hashlib
import json
from typing import Any


def execute_payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_execute_payload(
    *,
    plan_id: str,
    plan_version: int,
    content_hash: str,
    project_id: str,
    source_root: str,
    git_base_commit: str,
    model_id: str,
    model_fast: str,
    sandbox_policy_version: str,
    validation_commands: list[str],
    reserved_eur_micros: int,
    correction_index: int,
    prior_execution_id: str | None,
    review_observations: str,
    prior_capture_sha: str | None,
) -> dict[str, Any]:
    return {
        "kind": "cursor_execute_v1",
        "plan_id": plan_id,
        "plan_version": plan_version,
        "content_hash": content_hash,
        "project_id": project_id,
        "source_root": source_root,
        "git_base_commit": git_base_commit,
        "model_id": model_id,
        "model_fast": model_fast,
        "sandbox_policy_version": sandbox_policy_version,
        "validation_commands": validation_commands,
        "reserved_eur_micros": reserved_eur_micros,
        "correction_index": correction_index,
        "prior_execution_id": prior_execution_id,
        "review_observations": review_observations,
        "prior_capture_sha": prior_capture_sha,
        "budget_note": (
            "DevCom reservation is not a Cursor provider hard cap. "
            "Timeout is not a financial guarantee."
        ),
    }


def integrate_payload_hash(
    *,
    execution_id: str,
    capture_manifest_sha: str,
    source_root: str,
    git_base_commit: str,
    branch_name: str,
) -> str:
    return execute_payload_hash(
        {
            "kind": "cursor_integrate_v1",
            "execution_id": execution_id,
            "capture_manifest_sha": capture_manifest_sha,
            "source_root": source_root,
            "git_base_commit": git_base_commit,
            "branch_name": branch_name,
        }
    )
