from __future__ import annotations

import subprocess
from pathlib import Path

from devcom.modules.projects.domain.code_artifacts import GitCaptureMeta

GIT_NOTE = (
    "Git commit describes the capture environment; it does not prove selected "
    "files match that commit, especially when the working tree is dirty."
)


def capture_git_meta(root: Path) -> GitCaptureMeta:
    commit = _run_git(root, ["rev-parse", "HEAD"])
    if commit is None:
        return GitCaptureMeta(commit=None, dirty=None, note=GIT_NOTE)
    status = _run_git(root, ["status", "--porcelain"])
    dirty = status is not None and status.strip() != ""
    return GitCaptureMeta(commit=commit.strip(), dirty=dirty, note=GIT_NOTE)


def _run_git(root: Path, args: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout
