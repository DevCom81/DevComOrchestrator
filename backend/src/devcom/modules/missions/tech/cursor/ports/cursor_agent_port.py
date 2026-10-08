from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class AgentInvokeResult:
    status: str
    agent_id: str
    run_id: str
    assistant_text: str
    usage: dict[str, Any] | None
    billed: dict[str, Any] | None
    billed_error: str | None
    writes_stable: bool


class CursorAgentPort(Protocol):
    def invoke_once(
        self,
        *,
        worktree: Path,
        prompt: str,
        model_id: str,
        model_fast: str,
    ) -> AgentInvokeResult: ...

    def cancel(self, *, agent_id: str, run_id: str) -> bool: ...

    def try_reconnect(self, *, agent_id: str, run_id: str) -> str | None:
        """Return known status or None if reconnect impossible."""
        ...
