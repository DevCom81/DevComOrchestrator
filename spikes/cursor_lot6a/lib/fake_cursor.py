from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

HELLO_BODY = '''\
def greet(name: str) -> str:
    return f"hello, {name}"
'''

TEST_BODY = '''\
from hello import greet


def test_greet() -> None:
    assert greet("devcom") == "hello, devcom"
'''


@dataclass(frozen=True, slots=True)
class FakeRunResult:
    status: str
    agent_id: str
    run_id: str
    touched: tuple[str, ...]


def apply_requested_change(worktree: Path) -> FakeRunResult:
    """Double: applies the micro-task without calling Cursor."""
    (worktree / "hello.py").write_text(HELLO_BODY, encoding="utf-8")
    (worktree / "test_hello.py").write_text(TEST_BODY, encoding="utf-8")
    return FakeRunResult(
        status="finished",
        agent_id="agent-fake",
        run_id="run-fake-1",
        touched=("hello.py", "test_hello.py"),
    )


def apply_new_file_only(worktree: Path) -> FakeRunResult:
    path = worktree / "notes_spike.txt"
    path.write_text("fixture note — no personal data\n", encoding="utf-8")
    return FakeRunResult(
        status="finished",
        agent_id="agent-fake",
        run_id="run-fake-new",
        touched=("notes_spike.txt",),
    )
