from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.return_artifacts import (
    CursorReturnArtifactStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.domain.diff_verify import verify_unified_diff
from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorNotFoundError,
    CursorValidationError,
)
from devcom.modules.missions.tech.cursor.domain.status import (
    DIFF_MAX_BYTES,
    REPORT_MAX_BYTES,
    VerificationStatus,
)
from devcom.modules.missions.tech.ports.code_snapshot_port import CodeSnapshotPort
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class ImportCursorReturnCommand:
    plan_id: str
    export_id: str
    report_text: str
    diff_text: str
    declared_base: str | None = None
    declared_commit: str | None = None


class ImportCursorReturn:
    def __init__(
        self,
        *,
        plans: SqlAlchemyCursorStore,
        artifacts: CursorReturnArtifactStore,
        snapshots: CodeSnapshotPort | None,
        policy: PermissionPolicy,
        clock: Clock,
    ) -> None:
        self._plans = plans
        self._artifacts = artifacts
        self._snapshots = snapshots
        self._policy = policy
        self._clock = clock

    def execute(self, command: ImportCursorReturnCommand) -> dict[str, Any]:
        require_tech_action(self._policy, "cursor.return.import")
        plan = self._plans.get_plan(command.plan_id)
        if plan is None:
            raise CursorNotFoundError("cursor plan not found")
        export = self._plans.get_export(command.export_id)
        if export is None or export["plan_id"] != plan.id:
            raise CursorConflictError("export does not belong to this plan")
        report = _utf8_bounded(command.report_text, REPORT_MAX_BYTES, "rapport")
        diff = _utf8_bounded(command.diff_text, DIFF_MAX_BYTES, "diff")
        snapshot = None
        git_commit = None
        if plan.code_snapshot_id and self._snapshots is not None:
            snapshot = self._snapshots.get(plan.project_id, plan.code_snapshot_id)
            if snapshot is not None:
                git_commit = snapshot.git.commit
        verified = verify_unified_diff(
            diff.decode("utf-8"),
            snapshot=snapshot,
            declared_commit=command.declared_commit,
            snapshot_git_commit=git_commit,
        )
        return_id, artifact_dir, report_sha, diff_sha = self._artifacts.write_pair(
            report=report, diff=diff
        )
        now = self._clock.now()
        payload = {
            "id": return_id,
            "plan_id": plan.id,
            "export_id": export["id"],
            "project_id": plan.project_id,
            "report_sha256": report_sha,
            "diff_sha256": diff_sha,
            "report_bytes": len(report),
            "diff_bytes": len(diff),
            "declared_base": command.declared_base,
            "declared_commit": command.declared_commit,
            "verification_status": verified.status.value,
            "verification_notes": verified.notes,
            "artifact_dir": artifact_dir,
            "linked_review_id": None,
            "imported_at": now,
        }
        self._plans.save_return(payload)
        plan.mark_return_imported(now)
        self._plans.save_plan(plan)
        return payload


def _utf8_bounded(text: str, max_bytes: int, label: str) -> bytes:
    if "\x00" in text:
        raise CursorValidationError(f"{label} : NUL interdit")
    try:
        raw = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CursorValidationError(f"{label} doit être UTF-8 strict") from exc
    if len(raw) > max_bytes:
        raise CursorValidationError(
            f"{label} dépasse {max_bytes} octets ({len(raw)}) — "
            f"{VerificationStatus.REJECTED_BOUNDS.value}"
        )
    return raw
