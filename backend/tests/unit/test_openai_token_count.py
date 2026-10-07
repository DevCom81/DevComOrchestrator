from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from devcom.modules.missions.tech.adapters.openai_token_count import (
    _http_count,
    count_kwargs,
    extract_input_tokens,
)
from devcom.modules.missions.tech.ports.llm_completion import LlmRequest


def _request() -> LlmRequest:
    return LlmRequest(
        step_key="analyze:architecte",
        agent_id="architecte",
        capability_id="tech.analyze.architecture",
        model_id="gpt-6.1-sol",
        effort="low",
        system_prompt="Tu es Architecte.",
        user_payload={"request_text": "court"},
        json_schema={"type": "object", "properties": {}, "additionalProperties": False},
        max_output_tokens=2500,
        max_input_tokens=4000,
    )


def test_count_kwargs_include_schema_and_prompt() -> None:
    body = count_kwargs(_request())
    assert body["model"] == "gpt-6.1-sol"
    assert body["reasoning"]["effort"] == "low"
    assert body["text"]["format"]["type"] == "json_schema"
    assert "schema" in body["text"]["format"]
    assert body["input"][0]["role"] == "system"


def test_extract_input_tokens_from_dict_and_object() -> None:
    assert extract_input_tokens({"input_tokens": 42}) == 42
    assert extract_input_tokens(SimpleNamespace(input_tokens=7)) == 7
    assert extract_input_tokens({"input_tokens": "x"}) is None
    assert extract_input_tokens({}) is None


def test_http_count_parses_official_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, int | str]:
            return {"object": "response.input_tokens", "input_tokens": 321}

    def fake_post(*_args: object, **_kwargs: object) -> FakeResponse:
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    counted = _http_count("sk-test", count_kwargs(_request()), 30.0)
    assert counted == 321
