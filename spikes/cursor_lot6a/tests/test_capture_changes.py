from __future__ import annotations

import subprocess
from pathlib import Path

from lib.capture_changes import capture_worktree, combined_change_report
from lib.fake_cursor import apply_new_file_only, apply_requested_change


def _git_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    (repo / "hello.py").write_text("def greet(name: str) -> str:\n    return name\n")
    subprocess.run(["git", "add", "hello.py"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "b"],
        cwd=repo,
        check=True,
    )
    return repo


def test_capture_tracked_and_new(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    apply_requested_change(repo)
    apply_new_file_only(repo)
    out = tmp_path / "out"
    result = capture_worktree(repo, out)
    assert result.unstaged_diff_sha
    assert "notes_spike.txt" in result.new_files
    assert (out / "new_files" / "notes_spike.txt").is_file()
    report = combined_change_report(result, export_id="e1")
    assert b"export_id" in report
    assert b"not proof" in report.lower() or b"not proof" in report
