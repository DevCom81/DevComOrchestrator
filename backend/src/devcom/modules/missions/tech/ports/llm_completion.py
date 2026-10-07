from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class LlmRequest:
    step_key: str
    agent_id: str
    capability_id: str
    model_id: str
    effort: str
    system_prompt: str
    user_payload: dict[str, Any]
    json_schema: dict[str, Any]
    max_output_tokens: int
    max_input_tokens: int


@dataclass(frozen=True, slots=True)
class LlmUsage:
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int


@dataclass(frozen=True, slots=True)
class LlmResult:
    ok: bool
    parsed: dict[str, Any] | None
    usage: LlmUsage | None
    error_code: str | None
    error_message: str | None
    provider_refusal: bool = False


class LlmCompletionPort(Protocol):
    def complete(self, request: LlmRequest) -> LlmResult:
        """Execute one bounded completion; no automatic retries."""

    def count_input_tokens(self, request: LlmRequest) -> tuple[int | None, str]:
        """Return (count, method_label). count None => unreliable."""
