from __future__ import annotations

import subprocess
from pathlib import Path

from lib.fake_cursor import apply_requested_change
from lib.local_validate import run_pytest_fixture


def test_fake_change_passes_pytest(tmp_path: Path) -> None:
    work = tmp_path / "w"
    work.mkdir()
    apply_requested_change(work)
    record = run_pytest_fixture(work, tmp_path / "v.log")
    assert record.exit_code == 0
    assert record.command[0] == "python"
    assert record.log_sha256
    assert "exit_code: 0" in (tmp_path / "v.log").read_text(encoding="utf-8")


def test_smoke_guard_blocks_without_env(tmp_path: Path) -> None:
    import os

    script = Path(__file__).resolve().parents[1] / "scripts" / "smoke_real_guard.py"
    env = {"PATH": os.environ.get("PATH", "/usr/bin")}
    proc = subprocess.run(
        ["python", str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 2
