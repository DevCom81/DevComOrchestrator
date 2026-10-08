from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from lib.bounded_io import (
    DEFAULT_MAX_FILE_BYTES,
    DEFAULT_MAX_TOTAL_BYTES,
    BoundExceededError,
    read_bounded,
    sha256_bytes,
    write_bounded,
)


@dataclass(frozen=True, slots=True)
class CaptureLimits:
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES


@dataclass(frozen=True, slots=True)
class CaptureResult:
    manifest_path: Path
    unstaged_diff_sha: str
    staged_diff_sha: str
    new_files: tuple[str, ...]
    total_bytes: int


def capture_worktree(
    repo: Path,
    out_dir: Path,
    *,
    limits: CaptureLimits | None = None,
) -> CaptureResult:
    bounds = limits or CaptureLimits()
    out_dir.mkdir(parents=True, exist_ok=True)
    u_sha, s_sha, total = _write_diffs(repo, out_dir, bounds)
    new_names, new_meta, total = _write_new_files(repo, out_dir, bounds, total)
    manifest = {
        "note": "Hashes prove integrity of captured bytes, not truth of agent claims.",
        "unstaged_diff_sha256": u_sha,
        "staged_diff_sha256": s_sha,
        "new_files": new_meta,
        "total_bytes": total,
    }
    body = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode()
    m_path = out_dir / "capture_manifest.json"
    write_bounded(m_path, body, max_bytes=bounds.max_file_bytes)
    return CaptureResult(
        manifest_path=m_path,
        unstaged_diff_sha=u_sha,
        staged_diff_sha=s_sha,
        new_files=tuple(new_names),
        total_bytes=total,
    )


def _write_diffs(
    repo: Path, out_dir: Path, bounds: CaptureLimits
) -> tuple[str, str, int]:
    unstaged = _git_output(repo, ["diff", "--binary"])
    staged = _git_output(repo, ["diff", "--cached", "--binary"])
    total = _check_size(unstaged, bounds) + _check_size(staged, bounds)
    u_sha = write_bounded(
        out_dir / "unstaged.diff", unstaged, max_bytes=bounds.max_file_bytes
    )
    s_sha = write_bounded(
        out_dir / "staged.diff", staged, max_bytes=bounds.max_file_bytes
    )
    return u_sha, s_sha, total


def _write_new_files(
    repo: Path,
    out_dir: Path,
    bounds: CaptureLimits,
    total: int,
) -> tuple[list[str], list[dict[str, object]], int]:
    new_names = _list_untracked(repo)
    new_meta: list[dict[str, object]] = []
    for rel in new_names:
        blob = read_bounded(repo / rel, max_bytes=bounds.max_file_bytes)
        total += len(blob)
        if total > bounds.max_total_bytes:
            raise BoundExceededError("total capture exceeds limit")
        dest = out_dir / "new_files" / rel
        digest = write_bounded(dest, blob, max_bytes=bounds.max_file_bytes)
        new_meta.append({"path": rel, "sha256": digest, "bytes": len(blob)})
    return new_names, new_meta, total


def _git_output(repo: Path, args: list[str]) -> bytes:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return proc.stdout


def _list_untracked(repo: Path) -> list[str]:
    raw = _git_output(repo, ["ls-files", "--others", "--exclude-standard"])
    lines = raw.decode("utf-8", errors="replace").splitlines()
    return [line for line in lines if line.strip()]


def _check_size(data: bytes, limits: CaptureLimits) -> int:
    if len(data) > limits.max_file_bytes:
        raise BoundExceededError(f"diff chunk {len(data)} > {limits.max_file_bytes}")
    return len(data)


def combined_change_report(capture: CaptureResult, *, export_id: str) -> bytes:
    text = (
        f"# Spike return report\n\n"
        f"- export_id: `{export_id}`\n"
        f"- unstaged_diff_sha256: `{capture.unstaged_diff_sha}`\n"
        f"- staged_diff_sha256: `{capture.staged_diff_sha}`\n"
        f"- new_files: {list(capture.new_files)}\n"
        f"- total_bytes: {capture.total_bytes}\n\n"
        "This report is hashed for integrity. Claims inside agent text are not proof.\n"
    )
    return text.encode("utf-8")


def report_digest(report: bytes) -> str:
    return sha256_bytes(report)
