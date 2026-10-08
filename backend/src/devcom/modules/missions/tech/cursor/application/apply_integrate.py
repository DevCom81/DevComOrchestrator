from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from devcom.modules.approvals.adapters.sqlalchemy_store import SqlAlchemyApprovalStore
from devcom.modules.approvals.domain.errors import ApprovalNotFoundError
from devcom.modules.approvals.domain.status import ACTION_CURSOR_INTEGRATE
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.git_workspace import (
    commit_all,
    prepare_integrate_worktree,
    require_clean_git_base,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_execution_store import (
    SqlAlchemyExecutionStore,
)
from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorNotFoundError,
    CursorValidationError,
)
from devcom.modules.missions.tech.cursor.domain.execute_canon import integrate_payload_hash
from devcom.modules.missions.tech.cursor.domain.integration import CursorIntegration
from devcom.shared.time import Clock

GIT_NAME = "DevCom Cursor"
GIT_EMAIL = "cursor-integrate@devcom.local"


@dataclass(frozen=True, slots=True)
class ApplyIntegrateCommand:
    execution_id: str
    approval_id: str
    idempotency_key: str
    runs_root: Path


class ApplyIntegrate:
    """Apply capture into attached repo via isolated git worktree + local commit.

    Does not touch the daily working tree, merge, or push.
    """

    def __init__(
        self,
        *,
        executions: SqlAlchemyExecutionStore,
        approvals: SqlAlchemyApprovalStore,
        policy: PermissionPolicy,
        clock: Clock,
    ) -> None:
        self._executions = executions
        self._approvals = approvals
        self._policy = policy
        self._clock = clock

    def execute(self, command: ApplyIntegrateCommand) -> CursorIntegration:
        require_tech_action(self._policy, "cursor.integrate.apply")
        existing = self._executions.get_integration_by_idempotency(command.idempotency_key)
        if existing is not None:
            return existing
        execution = self._executions.get(command.execution_id)
        if execution is None:
            raise CursorNotFoundError("execution not found")
        if not execution.capture_manifest_sha or execution.capture_incomplete:
            raise CursorConflictError("execution capture incomplete — cannot integrate")
        approval = self._approvals.get(command.approval_id)
        if approval is None:
            raise ApprovalNotFoundError("approval not found")
        if approval.action_id != ACTION_CURSOR_INTEGRATE:
            raise CursorConflictError("approval is not an integrate GO")
        branch = f"devcom/cursor/{execution.id}"
        digest = integrate_payload_hash(
            execution_id=execution.id,
            capture_manifest_sha=execution.capture_manifest_sha,
            source_root=execution.source_root,
            git_base_commit=execution.git_base_commit,
            branch_name=branch,
        )
        now = self._clock.now()
        approval.consume_granted(
            payload_hash=digest,
            resource_version=1,
            now=now,
            mismatch_message="integrate GO does not match execution capture",
        )
        self._approvals.save(approval)
        item = CursorIntegration.create(
            execution_id=execution.id,
            approval_id=approval.id,
            payload_hash=digest,
            branch_name=branch,
            idempotency_key=command.idempotency_key,
            now=now,
        )
        self._executions.save_integration(item)
        dest = command.runs_root / execution.id / "integrate_wt"
        try:
            require_clean_git_base(Path(execution.source_root))
            prepare_integrate_worktree(
                source_root=Path(execution.source_root),
                dest=dest,
                branch_name=branch,
                base_commit=execution.git_base_commit,
            )
            _apply_capture_tree(
                capture_dir=command.runs_root / execution.id / "capture",
                dest=dest,
            )
            sha = commit_all(
                dest,
                message=f"devcom cursor integrate {execution.id}",
                name=GIT_NAME,
                email=GIT_EMAIL,
            )
        except (CursorConflictError, CursorValidationError, OSError) as exc:
            item.mark_failed(str(exc), self._clock.now())
            self._executions.save_integration(item)
            return item
        hint = (
            f"cd {execution.source_root} && git fetch . {branch} "
            f"&& git cherry-pick {sha}"
        )
        item.mark_applied(
            commit_sha=sha,
            worktree_path=str(dest),
            summary=f"Local commit {sha[:12]} on {branch}",
            merge_hint=hint,
            now=self._clock.now(),
        )
        self._executions.save_integration(item)
        return item


def _apply_capture_tree(*, capture_dir: Path, dest: Path) -> None:
    """Apply new_files from capture; patch application via vs_base diff if present."""
    new_root = capture_dir / "new_files"
    if new_root.is_dir():
        for path in new_root.rglob("*"):
            if path.is_file():
                rel = path.relative_to(new_root)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    vs_base = capture_dir / "vs_base_commits.diff"
    unstaged = capture_dir / "unstaged.diff"
    for diff_path in (vs_base, unstaged):
        if diff_path.is_file() and diff_path.stat().st_size > 0:
            _git_apply(dest, diff_path)


def _git_apply(cwd: Path, diff_path: Path) -> None:
    import subprocess

    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", str(diff_path)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        # unstaged may duplicate vs_base — ignore empty / already applied
        if "already exists" in (proc.stderr or "") or "patch does not apply" in (
            proc.stderr or ""
        ):
            return
        raise CursorConflictError(proc.stderr.strip() or "git apply failed")
