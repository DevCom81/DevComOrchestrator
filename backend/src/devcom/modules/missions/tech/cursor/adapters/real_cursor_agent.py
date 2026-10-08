from __future__ import annotations

from pathlib import Path
from typing import Any

from devcom.modules.missions.tech.cursor.domain.errors import CursorConflictError
from devcom.modules.missions.tech.cursor.ports.cursor_agent_port import AgentInvokeResult


class RealCursorAgent:
    def __init__(self, *, api_key: str) -> None:
        if not api_key.strip():
            raise CursorConflictError("CURSOR_API_KEY required for real cursor adapter")
        self._api_key = api_key.strip()

    def invoke_once(
        self,
        *,
        worktree: Path,
        prompt: str,
        model_id: str,
        model_fast: str,
    ) -> AgentInvokeResult:
        from cursor_sdk import (
            Agent,
            LocalAgentOptions,
            ModelParameterValue,
            ModelSelection,
            SandboxOptions,
        )

        model = ModelSelection(
            id=model_id,
            params=(ModelParameterValue(id="fast", value=model_fast),),
        )
        local = LocalAgentOptions(
            cwd=str(worktree),
            setting_sources=("project",),
            sandbox_options=SandboxOptions(enabled=True),
        )
        with Agent.create(
            model=model,
            api_key=self._api_key,
            name="devcom-cursor-execution",
            local=local,
        ) as agent:
            run = agent.send(prompt)
            result = run.wait()
            usage = _usage_dict(getattr(result, "usage", None) or run.usage)
            billed, err = _safe_usage(agent)
            status = str(result.status)
            stable = status in {"finished", "cancelled", "error"}
            return AgentInvokeResult(
                status=status,
                agent_id=str(result.agent_id or agent.agent_id),
                run_id=str(result.id),
                assistant_text=str(result.result or ""),
                usage=usage,
                billed=billed,
                billed_error=err,
                writes_stable=stable,
            )

    def cancel(self, *, agent_id: str, run_id: str) -> bool:
        from cursor_sdk import Agent, CursorSDKError

        del agent_id
        try:
            Agent.cancel_run(run_id)
            return True
        except CursorSDKError:
            return False

    def try_reconnect(self, *, agent_id: str, run_id: str) -> str | None:
        from cursor_sdk import Agent, CursorSDKError

        try:
            run = Agent.get_run(run_id)
            del agent_id
            return str(getattr(run, "status", None) or "uncertain")
        except CursorSDKError:
            return None


def _usage_dict(usage: object | None) -> dict[str, Any] | None:
    if usage is None:
        return None
    return {
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "cache_read_tokens": getattr(usage, "cache_read_tokens", None),
    }


def _safe_usage(agent: object) -> tuple[dict[str, Any] | None, str | None]:
    from cursor_sdk import CursorSDKError

    try:
        raw = agent.get_usage()  # type: ignore[attr-defined]
    except CursorSDKError as exc:
        return None, f"{type(exc).__name__}: {exc}"
    cost = getattr(raw, "cost", None)
    return {
        "usage": _usage_dict(getattr(raw, "usage", None)),
        "cost": None
        if cost is None
        else {
            "raw_cost_cents": getattr(cost, "raw_cost_cents", None),
            "charged_cents": getattr(cost, "charged_cents", None),
        },
    }, None
