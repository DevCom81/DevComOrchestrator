from __future__ import annotations

from pathlib import Path

from lib.fake_cursor import apply_requested_change
from lib.invoke_result import InvokeResult


def fake_invoker(worktree: Path, prompt: str) -> InvokeResult:
    del prompt  # double ignores prompt content; applies known change
    fake = apply_requested_change(worktree)
    return InvokeResult(
        status=fake.status,
        agent_id=fake.agent_id,
        run_id=fake.run_id,
        assistant_text="fake: applied greet implementation (not a real Cursor run)",
        model_id="fake-model",
        duration_ms=0,
        usage={"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0},
        billed_usage=None,
        billed_usage_error="n/a for fake",
        git_info=None,
    )
