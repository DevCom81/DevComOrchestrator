from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from lib.bounded_io import DEFAULT_MAX_FILE_BYTES, write_bounded
from lib.capture_changes import (
    CaptureResult,
    capture_worktree,
    combined_change_report,
    report_digest,
)
from lib.invoke_result import InvokeResult
from lib.local_validate import ValidationRecord, run_pytest_fixture

ExportId = str
Invoker = Callable[[Path, str], InvokeResult]


@dataclass(frozen=True, slots=True)
class SmokeOutcome:
    worktree: Path
    artifacts: Path
    invoke: InvokeResult
    capture: CaptureResult
    report_sha256: str
    validation: ValidationRecord
    export_id: ExportId


def prepare_fresh_worktree(root: Path, run_id: str) -> Path:
    fixture = root / "fixture"
    if not (fixture / ".git").is_dir():
        raise RuntimeError("fixture/.git missing — run scripts/init_fixture_git.sh")
    dest = root / "worktrees" / run_id
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--local", str(fixture), str(dest)],
        check=True,
        capture_output=True,
    )
    return dest


def build_prompt(worktree: Path) -> str:
    package = (worktree / "PACKAGE.md").read_text(encoding="utf-8")
    return (
        "You are implementing a bounded spike task. Follow PACKAGE.md exactly.\n"
        "Edit only hello.py and test_hello.py if needed. No git push. No network.\n"
        "Do not claim tests passed; the orchestrator will run pytest.\n\n"
        f"{package}\n"
    )


def run_smoke_flow(
    *,
    root: Path,
    run_id: str,
    export_id: ExportId,
    invoker: Invoker,
) -> SmokeOutcome:
    worktree = prepare_fresh_worktree(root, run_id)
    arts = root / "artifacts" / run_id
    if arts.exists():
        shutil.rmtree(arts)
    arts.mkdir(parents=True)
    prompt = build_prompt(worktree)
    write_bounded(
        arts / "prompt_sent.md",
        prompt.encode("utf-8"),
        max_bytes=DEFAULT_MAX_FILE_BYTES,
    )
    invoke = invoker(worktree, prompt)
    _write_json(arts / "invoke_result.json", _invoke_public(invoke))
    if invoke.assistant_text:
        write_bounded(
            arts / "assistant_text.txt",
            invoke.assistant_text.encode("utf-8"),
            max_bytes=DEFAULT_MAX_FILE_BYTES,
        )
    capture = capture_worktree(worktree, arts / "capture")
    report = combined_change_report(capture, export_id=export_id)
    report_sha = report_digest(report)
    write_bounded(arts / "return_report.md", report, max_bytes=DEFAULT_MAX_FILE_BYTES)
    validation = run_pytest_fixture(worktree, arts / "validation.log")
    summary = {
        "export_id": export_id,
        "invoke_status": invoke.status,
        "agent_id": invoke.agent_id,
        "run_id": invoke.run_id,
        "report_sha256": report_sha,
        "validation_exit": validation.exit_code,
        "validation_log_sha256": validation.log_sha256,
        "new_files": list(capture.new_files),
        "note": "Assistant text is declared, not proof. Capture+validation are proofs.",
    }
    _write_json(arts / "smoke_summary.json", summary)
    return SmokeOutcome(
        worktree=worktree,
        artifacts=arts,
        invoke=invoke,
        capture=capture,
        report_sha256=report_sha,
        validation=validation,
        export_id=export_id,
    )


def _invoke_public(invoke: InvokeResult) -> dict[str, object]:
    data = asdict(invoke)
    # Keep assistant text out of the JSON summary size; stored separately.
    data["assistant_text"] = f"<{len(invoke.assistant_text)} chars>"
    return data


def _write_json(path: Path, payload: dict[str, object]) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode()
    write_bounded(path, body, max_bytes=DEFAULT_MAX_FILE_BYTES)
