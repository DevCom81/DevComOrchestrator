from __future__ import annotations

import subprocess
from pathlib import Path

from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorValidationError,
)


def require_clean_git_base(source_root: Path) -> str:
    root = source_root.resolve()
    if not (root / ".git").exists() and not _is_worktree(root):
        raise CursorValidationError("attached source root must be a git repository")
    status = _git(root, ["status", "--porcelain"])
    if status.strip():
        raise CursorConflictError(
            "git working tree is dirty — prepare a clean base commit before execute"
        )
    commit = _git(root, ["rev-parse", "HEAD"]).strip()
    if len(commit) < 7:
        raise CursorValidationError("unable to resolve HEAD commit")
    return commit


def prepare_execution_worktree(
    *,
    source_root: Path,
    dest: Path,
    base_commit: str,
) -> Path:
    if dest.exists():
        raise CursorConflictError(f"worktree path already exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    head = require_clean_git_base(source_root)
    if head != base_commit:
        raise CursorConflictError(
            "source root HEAD does not match approved git base — re-prepare execute GO"
        )
    _git(source_root, ["worktree", "add", "--detach", str(dest), base_commit])
    return dest


def prepare_integrate_worktree(
    *,
    source_root: Path,
    dest: Path,
    branch_name: str,
    base_commit: str,
) -> Path:
    if dest.exists():
        raise CursorConflictError(f"integrate worktree exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    head = require_clean_git_base(source_root)
    if head != base_commit:
        raise CursorConflictError("integrate base commit mismatch — refresh GO")
    _git(
        source_root,
        ["worktree", "add", "-b", branch_name, str(dest), base_commit],
    )
    return dest


def commit_all(
    worktree: Path,
    *,
    message: str,
    name: str,
    email: str,
) -> str:
    _git(worktree, ["add", "-A"])
    env_extra = {
        "GIT_AUTHOR_NAME": name,
        "GIT_AUTHOR_EMAIL": email,
        "GIT_COMMITTER_NAME": name,
        "GIT_COMMITTER_EMAIL": email,
    }
    _git(worktree, ["commit", "-m", message], env=env_extra)
    return _git(worktree, ["rev-parse", "HEAD"]).strip()


def _is_worktree(root: Path) -> bool:
    git = root / ".git"
    return git.is_file()


def _git(
    cwd: Path,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
) -> str:
    import os

    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=merged,
        check=False,
    )
    if proc.returncode != 0:
        raise CursorConflictError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout
