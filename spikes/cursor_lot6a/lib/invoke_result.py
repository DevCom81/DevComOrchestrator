from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class InvokeResult:
    status: str
    agent_id: str
    run_id: str
    assistant_text: str
    model_id: str | None
    duration_ms: int | None
    usage: dict[str, Any] | None
    billed_usage: dict[str, Any] | None
    billed_usage_error: str | None
    git_info: dict[str, Any] | None
