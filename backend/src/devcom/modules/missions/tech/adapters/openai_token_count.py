from __future__ import annotations

from typing import Any

from devcom.modules.missions.tech.ports.llm_completion import LlmRequest


def count_kwargs(request: LlmRequest) -> dict[str, Any]:
    """Same billable input shape as responses.create (schema included)."""
    return {
        "model": request.model_id,
        "reasoning": {"effort": request.effort},
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
                        "text": _user_text(request),
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


def extract_input_tokens(payload: Any) -> int | None:
    if isinstance(payload, dict):
        value = payload.get("input_tokens")
        return value if isinstance(value, int) else None
    value = getattr(payload, "input_tokens", None)
    return value if isinstance(value, int) else None


def count_via_sdk_or_http(client: Any, request: LlmRequest, api_key: str, timeout_s: float) -> int:
    body = count_kwargs(request)
    via_sdk = _try_sdk_count(client, body)
    if via_sdk is not None:
        return via_sdk
    return _http_count(api_key, body, timeout_s)


def _user_text(request: LlmRequest) -> str:
    import json

    return json.dumps(request.user_payload, ensure_ascii=False)


def _try_sdk_count(client: Any, body: dict[str, Any]) -> int | None:
    resource = getattr(client.responses, "input_tokens", None)
    if resource is None:
        resource = getattr(client.responses, "inputTokens", None)
    if resource is None:
        return None
    count_fn = getattr(resource, "count", None)
    if not callable(count_fn):
        if callable(resource):
            return extract_input_tokens(resource(**body))
        return None
    return extract_input_tokens(count_fn(**body))


def _http_count(api_key: str, body: dict[str, Any], timeout_s: float) -> int:
    import httpx

    response = httpx.post(
        "https://api.openai.com/v1/responses/input_tokens",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=timeout_s,
    )
    response.raise_for_status()
    counted = extract_input_tokens(response.json())
    if counted is None:
        raise ValueError("responses/input_tokens returned no input_tokens int")
    return counted
