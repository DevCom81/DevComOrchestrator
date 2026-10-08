from __future__ import annotations

import subprocess
from pathlib import Path

from lib.fake_invoke import fake_invoker
from lib.smoke_flow import run_smoke_flow


def _init_fixture(root: Path) -> None:
    fixture = root / "fixture"
    fixture.mkdir()
    (fixture / "hello.py").write_text(
        "def greet(name: str) -> str:\n    raise NotImplementedError\n",
        encoding="utf-8",
    )
    (fixture / "test_hello.py").write_text(
        "from hello import greet\n\n"
        "def test_greet() -> None:\n"
        '    assert greet("devcom") == "hello, devcom"\n',
        encoding="utf-8",
    )
    (fixture / "PACKAGE.md").write_text("# spike\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main"], cwd=fixture, check=True)
    subprocess.run(["git", "add", "."], cwd=fixture, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "b"],
        cwd=fixture,
        check=True,
    )


def test_smoke_flow_with_fake(tmp_path: Path) -> None:
    _init_fixture(tmp_path)
    outcome = run_smoke_flow(
        root=tmp_path,
        run_id="t1",
        export_id="export-test",
        invoker=fake_invoker,
    )
    assert outcome.invoke.status == "finished"
    assert outcome.validation.exit_code == 0
    assert (outcome.artifacts / "smoke_summary.json").is_file()
    assert (outcome.artifacts / "capture" / "capture_manifest.json").is_file()
    assert outcome.report_sha256
