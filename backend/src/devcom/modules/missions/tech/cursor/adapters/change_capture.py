from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

MAX_FILE = 200 * 1024
MAX_TOTAL = 1 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class CaptureBundle:
    manifest_sha: str
    artifact_dir: Path
    report_text: str
    diff_text: str
    new_files: tuple[str, ...]
    deleted_files: tuple[str, ...]
    commits: tuple[str, ...]


def capture_full(repo: Path, out_dir: Path, *, base_commit: str) -> CaptureBundle:
    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    unstaged = _git_bytes(repo, ["diff", "--binary"])
    staged = _git_bytes(repo, ["diff", "--cached", "--binary"])
    vs_base = _git_bytes(repo, ["diff", "--binary", f"{base_commit}...HEAD"])
    total += _bound(unstaged) + _bound(staged) + _bound(vs_base)
    _write(out_dir / "unstaged.diff", unstaged)
    _write(out_dir / "staged.diff", staged)
    _write(out_dir / "vs_base_commits.diff", vs_base)
    deleted = _deleted_paths(repo, base_commit)
    new_files = _untracked(repo)
    for rel in new_files:
        data = (repo / rel).read_bytes()
        total += _bound(data)
        if total > MAX_TOTAL:
            raise ValueError("capture exceeds total byte limit")
        dest = out_dir / "new_files" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        _write(dest, data)
    commits = _commits_since(repo, base_commit)
    manifest = {
        "note": "Integrity hashes only — not proof of software correctness.",
        "base_commit": base_commit,
        "unstaged_sha256": _sha(unstaged),
        "staged_sha256": _sha(staged),
        "vs_base_sha256": _sha(vs_base),
        "new_files": [{"path": p, "sha256": _sha((out_dir / "new_files" / p).read_bytes())}
                      for p in new_files],
        "deleted_files": list(deleted),
        "commits": list(commits),
        "total_bytes": total,
    }
    body = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode()
    _write(out_dir / "capture_manifest.json", body)
    report = (
        f"# Cursor execution capture\n\n"
        f"- base: `{base_commit}`\n"
        f"- new_files: {list(new_files)}\n"
        f"- deleted: {list(deleted)}\n"
        f"- commits: {list(commits)}\n"
        f"- manifest_sha256: `{_sha(body)}`\n"
    )
    diff_text = vs_base.decode("utf-8", errors="replace")
    if unstaged:
        diff_text += "\n# unstaged\n" + unstaged.decode("utf-8", errors="replace")
    if staged:
        diff_text += "\n# staged\n" + staged.decode("utf-8", errors="replace")
    return CaptureBundle(
        manifest_sha=_sha(body),
        artifact_dir=out_dir,
        report_text=report,
        diff_text=diff_text,
        new_files=tuple(new_files),
        deleted_files=tuple(deleted),
        commits=tuple(commits),
    )


def _deleted_paths(repo: Path, base: str) -> list[str]:
    raw = _git_text(repo, ["diff", "--name-only", "--diff-filter=D", f"{base}...HEAD"])
    tracked = [line for line in raw.splitlines() if line.strip()]
    # also working tree deletions vs HEAD
    wt = _git_text(repo, ["ls-files", "--deleted"])
    for line in wt.splitlines():
        if line.strip() and line not in tracked:
            tracked.append(line)
    return tracked


def _untracked(repo: Path) -> list[str]:
    raw = _git_text(repo, ["ls-files", "--others", "--exclude-standard"])
    return [line for line in raw.splitlines() if line.strip()]


def _commits_since(repo: Path, base: str) -> list[str]:
    raw = _git_text(repo, ["rev-list", "--reverse", f"{base}..HEAD"])
    return [line for line in raw.splitlines() if line.strip()]


def _git_bytes(repo: Path, args: list[str]) -> bytes:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True)
    return proc.stdout


def _git_text(repo: Path, args: list[str]) -> str:
    return _git_bytes(repo, args).decode("utf-8", errors="replace")


def _bound(data: bytes) -> int:
    if len(data) > MAX_FILE:
        raise ValueError(f"chunk exceeds {MAX_FILE}")
    return len(data)


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _sha(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()
