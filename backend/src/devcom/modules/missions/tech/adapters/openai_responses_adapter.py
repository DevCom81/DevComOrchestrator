from __future__ import annotations

import json
import os
from typing import Any

from devcom.modules.missions.tech.adapters.openai_parse import parse_responses_result
from devcom.modules.missions.tech.adapters.openai_token_count import count_via_sdk_or_http
from devcom.modules.missions.tech.ports.llm_completion import LlmRequest, LlmResult


class OpenAIResponsesAdapter:
    """OpenAI Responses API adapter — max_retries=0, no tools."""

    def __init__(self, api_key: str | None = None, timeout_s: float = 120.0) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
        self._timeout_s = timeout_s

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def complete(self, request: LlmRequest) -> LlmResult:
        if not self._api_key:
            return LlmResult(
                ok=False,
                parsed=None,
                usage=None,
                error_code="missing_api_key",
                error_message="OPENAI_API_KEY absent",
            )
        try:
            from openai import OpenAI
        except ImportError:
            return LlmResult(
                ok=False,
                parsed=None,
                usage=None,
                error_code="sdk_missing",
                error_message="openai package not installed",
            )
        client = OpenAI(api_key=self._api_key, max_retries=0, timeout=self._timeout_s)
        try:
            response = client.responses.create(**_create_kwargs(request))
        except Exception as exc:  # noqa: BLE001 — mapped provider failure, never silent
            return LlmResult(
                ok=False,
                parsed=None,
                usage=None,
                error_code="provider_error",
                error_message=str(exc)[:500],
            )
        return parse_responses_result(response)

    def count_input_tokens(self, request: LlmRequest) -> tuple[int | None, str]:
        estimate = _char_estimate(request)
        if not self._api_key:
            return estimate, "char_div4_estimate_non_guaranteed"
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._api_key, max_retries=0, timeout=30.0)
            counted = count_via_sdk_or_http(
                client, request, self._api_key, timeout_s=30.0
            )
            return counted, "openai_responses_input_tokens"
        except Exception:  # noqa: BLE001 — refuse rather than claim a guarantee
            return estimate, "char_div4_estimate_non_guaranteed"


def _create_kwargs(request: LlmRequest) -> dict[str, Any]:
    return {
        "model": request.model_id,
        "reasoning": {"effort": request.effort},
        "max_output_tokens": request.max_output_tokens,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": request.system_prompt}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(request.user_payload, ensure_ascii=False),
                    }
                ],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": request.step_key.replace(":", "_")[:64],
                "strict": True,
                "schema": request.json_schema,
            }
        },
    }


def _char_estimate(request: LlmRequest) -> int:
    raw = request.system_prompt + json.dumps(
        {"payload": request.user_payload, "schema": request.json_schema},
        ensure_ascii=False,
    )
    return max(1, len(raw) // 4)
