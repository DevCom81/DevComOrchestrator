from __future__ import annotations

from pathlib import Path

from devcom.modules.missions.tech.cursor.adapters.change_capture import capture_full
from devcom.modules.missions.tech.cursor.adapters.execution_budget import (
    ExecutionBudgetGate,
)
from devcom.modules.missions.tech.cursor.adapters.return_artifacts import (
    CursorReturnArtifactStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_execution_store import (
    SqlAlchemyExecutionStore,
)
from devcom.modules.missions.tech.cursor.domain.execution import CursorExecution
from devcom.modules.missions.tech.cursor.domain.execution_status import ExecutionStatus
from devcom.modules.missions.tech.cursor.domain.status import VerificationStatus
from devcom.shared.time import Clock


def capture_and_attach_return(
    *,
    intent: CursorExecution,
    work: Path,
    runs_root: Path,
    plans: SqlAlchemyCursorStore,
    executions: SqlAlchemyExecutionStore,
    artifacts: CursorReturnArtifactStore,
    budget: ExecutionBudgetGate,
    clock: Clock,
) -> CursorExecution:
    out = runs_root / intent.id / "capture"
    bundle = capture_full(work, out, base_commit=intent.git_base_commit)
    intent.mark_capture(
        manifest_sha=bundle.manifest_sha,
        incomplete=False,
        now=clock.now(),
    )
    return_id, artifact_dir, report_sha, diff_sha = artifacts.write_pair(
        report=bundle.report_text.encode("utf-8"),
        diff=bundle.diff_text.encode("utf-8"),
    )
    payload = {
        "id": return_id,
        "plan_id": intent.plan_id,
        "export_id": None,
        "execution_id": intent.id,
        "project_id": intent.project_id,
        "report_sha256": report_sha,
        "diff_sha256": diff_sha,
        "report_bytes": len(bundle.report_text.encode()),
        "diff_bytes": len(bundle.diff_text.encode()),
        "declared_base": intent.git_base_commit,
        "declared_commit": None,
        "verification_status": VerificationStatus.UNVERIFIED.value,
        "verification_notes": (
            "Auto-captured from execution. Validation command/exit/logs are "
            "execution proofs, not absolute software correctness."
        ),
        "artifact_dir": artifact_dir,
        "linked_review_id": None,
        "imported_at": clock.now(),
    }
    plans.save_return(payload)
    intent.attach_return(return_id, clock.now())
    executions.save(intent)
    if intent.billed_json is None:
        budget.mark_uncertain(execution_id=intent.id)
    else:
        budget.release_unused(execution_id=intent.id)
    return intent


def build_execute_prompt(plan_markdown: str, payload_json: str) -> str:
    return (
        "Implement the approved Cursor package. Follow bounds strictly.\n"
        "No git push. Do not claim tests passed.\n\n"
        f"{plan_markdown}\n\n# Execute context\n```json\n{payload_json}\n```\n"
    )


def map_provider_status(raw: str, cancel_requested: bool) -> ExecutionStatus:
    if cancel_requested and raw in {"cancelled", "finished"}:
        return ExecutionStatus.CANCELLED
    if raw == "finished":
        return ExecutionStatus.FINISHED
    if raw == "cancelled":
        return ExecutionStatus.CANCELLED
    if raw in {"error", "failed"}:
        return ExecutionStatus.FAILED
    return ExecutionStatus.UNCERTAIN
