from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from lib.bounded_io import DEFAULT_MAX_FILE_BYTES, write_bounded


@dataclass(frozen=True, slots=True)
class ValidationRecord:
    command: tuple[str, ...]
    exit_code: int
    log_sha256: str
    log_path: Path


def run_pytest_fixture(worktree: Path, log_path: Path) -> ValidationRecord:
    command = ("python", "-m", "pytest", "-q", str(worktree / "test_hello.py"))
    proc = subprocess.run(
        list(command),
        cwd=worktree,
        capture_output=True,
        text=True,
    )
    log = (
        f"command: {' '.join(command)}\n"
        f"exit_code: {proc.returncode}\n"
        f"--- stdout ---\n{proc.stdout}\n"
        f"--- stderr ---\n{proc.stderr}\n"
    ).encode("utf-8")
    digest = write_bounded(log_path, log, max_bytes=DEFAULT_MAX_FILE_BYTES)
    return ValidationRecord(
        command=command,
        exit_code=proc.returncode,
        log_sha256=digest,
        log_path=log_path,
    )
