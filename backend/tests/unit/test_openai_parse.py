from __future__ import annotations

import json
from types import SimpleNamespace

from devcom.modules.missions.tech.adapters.openai_parse import parse_responses_result


def test_parse_ignores_reasoning_items_and_reads_message_json() -> None:
    payload = {
        "has_objection": False,
        "objection": "",
        "target_finding_id": "",
        "evidence_refs": [],
    }
    response = SimpleNamespace(
        status="completed",
        output_text=None,
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=20,
            output_tokens_details=SimpleNamespace(reasoning_tokens=5),
        ),
        output=[
            SimpleNamespace(
                type="reasoning",
                content=[SimpleNamespace(type="summary_text", text="thinking aloud {not json}")],
            ),
            SimpleNamespace(
                type="message",
                content=[
                    SimpleNamespace(
                        type="output_text",
                        text=json.dumps(payload),
                        parsed=None,
                    )
                ],
            ),
        ],
    )
    result = parse_responses_result(response)
    assert result.ok
    assert result.parsed == payload


def test_parse_prefers_structured_parsed_object() -> None:
    payload = {
        "has_objection": False,
        "objection": "",
        "target_finding_id": "",
        "evidence_refs": [],
    }
    response = SimpleNamespace(
        status="completed",
        output_text="not-json",
        usage=None,
        output=[
            SimpleNamespace(
                type="message",
                content=[
                    SimpleNamespace(type="output_text", text="broken", parsed=payload)
                ],
            )
        ],
    )
    result = parse_responses_result(response)
    assert result.ok
    assert result.parsed == payload


def test_parse_incomplete_reports_reason_with_usage() -> None:
    response = SimpleNamespace(
        status="incomplete",
        incomplete_details=SimpleNamespace(reason="max_output_tokens"),
        output_text="",
        usage=SimpleNamespace(
            input_tokens=11,
            output_tokens=12,
            output_tokens_details=None,
        ),
        output=[],
    )
    result = parse_responses_result(response)
    assert not result.ok
    assert result.error_code == "incomplete_output"
    assert "max_output_tokens" in (result.error_message or "")
    assert result.usage is not None
    assert result.usage.output_tokens == 12


def test_parse_refusal() -> None:
    response = SimpleNamespace(
        status="completed",
        output_text=None,
        usage=None,
        output=[
            SimpleNamespace(
                type="message",
                content=[SimpleNamespace(type="refusal", refusal="Nope")],
            )
        ],
    )
    result = parse_responses_result(response)
    assert not result.ok
    assert result.provider_refusal
    assert result.error_code == "provider_refusal"
