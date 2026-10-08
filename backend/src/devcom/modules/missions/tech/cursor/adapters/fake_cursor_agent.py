from __future__ import annotations

from pathlib import Path

from devcom.modules.missions.tech.cursor.ports.cursor_agent_port import AgentInvokeResult


class FakeCursorAgent:
    """Explicit demo/test double — never selected silently in real mode."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self._cancelled: set[str] = set()

    def invoke_once(
        self,
        *,
        worktree: Path,
        prompt: str,
        model_id: str,
        model_fast: str,
    ) -> AgentInvokeResult:
        del model_id, model_fast
        self.calls.append(prompt[:80])
        (worktree / "hello.py").write_text(
            'def greet(name: str) -> str:\n    return f"hello, {name}"\n',
            encoding="utf-8",
        )
        (worktree / "test_hello.py").write_text(
            "from hello import greet\n\n"
            "def test_greet() -> None:\n"
            '    assert greet("devcom") == "hello, devcom"\n',
            encoding="utf-8",
        )
        return AgentInvokeResult(
            status="finished",
            agent_id="agent-fake",
            run_id=f"run-fake-{len(self.calls)}",
            assistant_text="fake applied greet (declared only)",
            usage={"input_tokens": 10, "output_tokens": 5, "cache_read_tokens": 0},
            billed=None,
            billed_error="n/a for fake",
            writes_stable=True,
        )

    def cancel(self, *, agent_id: str, run_id: str) -> bool:
        self._cancelled.add(f"{agent_id}:{run_id}")
        return True

    def try_reconnect(self, *, agent_id: str, run_id: str) -> str | None:
        key = f"{agent_id}:{run_id}"
        if key in self._cancelled:
            return "cancelled"
        return "finished"
