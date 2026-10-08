from __future__ import annotations

from pathlib import Path
from typing import Any

from lib.invoke_result import InvokeResult

# Model: docs + forum — pin standard (non-fast) to avoid default fast billing.
SMOKE_MODEL_ID = "composer-2.5"
SMOKE_FAST_PARAM = "false"


def invoke_once(*, worktree: Path, prompt: str, api_key: str) -> InvokeResult:
    """Exactly one Agent.create + one send + wait. No retry."""
    from cursor_sdk import (
        Agent,
        LocalAgentOptions,
        ModelParameterValue,
        ModelSelection,
        SandboxOptions,
    )

    model = ModelSelection(
        id=SMOKE_MODEL_ID,
        params=(ModelParameterValue(id="fast", value=SMOKE_FAST_PARAM),),
    )
    local = LocalAgentOptions(
        cwd=str(worktree),
        setting_sources=("project",),
        sandbox_options=SandboxOptions(enabled=True),
    )
    with Agent.create(
        model=model,
        api_key=api_key,
        name="devcom-lot6a-smoke",
        local=local,
    ) as agent:
        run = agent.send(prompt)
        result = run.wait()
        usage = _token_usage_dict(getattr(result, "usage", None) or run.usage)
        billed, billed_err = _safe_get_usage(agent)
        git_info = _git_dict(getattr(result, "git", None))
        return InvokeResult(
            status=str(result.status),
            agent_id=str(result.agent_id or agent.agent_id),
            run_id=str(result.id),
            assistant_text=str(result.result or ""),
            model_id=_model_id(result.model) or SMOKE_MODEL_ID,
            duration_ms=int(result.duration_ms) if result.duration_ms else None,
            usage=usage,
            billed_usage=billed,
            billed_usage_error=billed_err,
            git_info=git_info,
        )


def _model_id(model: object | None) -> str | None:
    if model is None:
        return None
    return str(getattr(model, "id", None) or model)


def _token_usage_dict(usage: object | None) -> dict[str, Any] | None:
    if usage is None:
        return None
    return {
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "cache_read_tokens": getattr(usage, "cache_read_tokens", None),
    }


def _git_dict(git: object | None) -> dict[str, Any] | None:
    if git is None:
        return None
    branches = getattr(git, "branches", ()) or ()
    return {"branches": [str(item) for item in branches]}


def _safe_get_usage(agent: object) -> tuple[dict[str, Any] | None, str | None]:
    from cursor_sdk import CursorSDKError

    try:
        raw = agent.get_usage()  # type: ignore[attr-defined]
    except CursorSDKError as exc:
        return None, f"{type(exc).__name__}: {exc}"
    cost = getattr(raw, "cost", None)
    return {
        "usage": _token_usage_dict(getattr(raw, "usage", None)),
        "cost": None
        if cost is None
        else {
            "raw_cost_cents": getattr(cost, "raw_cost_cents", None),
            "charged_cents": getattr(cost, "charged_cents", None),
        },
        "runs_count": len(getattr(raw, "runs", ()) or ()),
    }, None
