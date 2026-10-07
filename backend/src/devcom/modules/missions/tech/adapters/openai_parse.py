from __future__ import annotations

import json
from typing import Any

from devcom.modules.missions.tech.ports.llm_completion import LlmResult, LlmUsage


def parse_responses_result(response: Any) -> LlmResult:
    usage = usage_from_response(response)
    status = getattr(response, "status", None)
    if status == "incomplete":
        reason = _incomplete_reason(response)
        return LlmResult(
            ok=False,
            parsed=None,
            usage=usage,
            error_code="incomplete_output",
            error_message=f"incomplete model output ({reason})",
        )
    refusal = _refusal_text(response)
    if refusal:
        return LlmResult(
            ok=False,
            parsed=None,
            usage=usage,
            error_code="provider_refusal",
            error_message=refusal[:500],
            provider_refusal=True,
        )
    structured = _structured_parsed(response)
    if isinstance(structured, dict):
        return LlmResult(
            ok=True, parsed=structured, usage=usage, error_code=None, error_message=None
        )
    text = _message_text(response)
    if not text:
        return LlmResult(
            ok=False,
            parsed=None,
            usage=usage,
            error_code="incomplete_output",
            error_message="empty message output (reasoning-only or missing)",
        )
    return _parse_json_object(text, usage)


def usage_from_response(response: Any) -> LlmUsage | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    details = getattr(usage, "output_tokens_details", None)
    reasoning = 0
    if details is not None:
        reasoning = int(getattr(details, "reasoning_tokens", 0) or 0)
    if reasoning > output_tokens:
        reasoning = output_tokens
    return LlmUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning,
    )


def _parse_json_object(text: str, usage: LlmUsage | None) -> LlmResult:
    candidate = text.strip().lstrip("\ufeff")
    if candidate.startswith("```"):
        candidate = _strip_fence(candidate)
    parsed = _loads_first_object(candidate)
    if parsed is None:
        preview = repr(candidate[:120])
        return LlmResult(
            ok=False,
            parsed=None,
            usage=usage,
            error_code="invalid_json",
            error_message=f"model output is not valid JSON: {preview}",
        )
    return LlmResult(
        ok=True, parsed=parsed, usage=usage, error_code=None, error_message=None
    )


def _loads_first_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    try:
        value, end = decoder.raw_decode(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start < 0:
            return None
        try:
            value, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            return None
        remainder = text[start + end :].strip()
    else:
        remainder = text[end:].strip()
    if remainder:
        return None
    if not isinstance(value, dict):
        return None
    return value


def _structured_parsed(response: Any) -> dict[str, Any] | None:
    """Prefer SDK Structured Outputs `parsed` on message content when present."""
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) not in {None, "message"}:
            continue
        for content in getattr(item, "content", []) or []:
            parsed = getattr(content, "parsed", None)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, str) and parsed.strip():
                loaded = _loads_first_object(parsed.strip())
                if loaded is not None:
                    return loaded
    return None


def _message_text(response: Any) -> str:
    """Prefer SDK output_text; else only message/output_text parts (never reasoning)."""
    direct = getattr(response, "output_text", None)
    if isinstance(direct, str) and direct.strip():
        return direct
    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) not in {None, "message"}:
            continue
        for content in getattr(item, "content", []) or []:
            ctype = getattr(content, "type", None)
            if ctype not in {None, "output_text", "text"}:
                continue
            text = getattr(content, "text", None)
            if isinstance(text, str) and text:
                chunks.append(text)
    return "".join(chunks)


def _refusal_text(response: Any) -> str | None:
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            if getattr(content, "type", None) == "refusal":
                refusal = getattr(content, "refusal", None)
                if isinstance(refusal, str) and refusal.strip():
                    return refusal
    return None


def _incomplete_reason(response: Any) -> str:
    details = getattr(response, "incomplete_details", None)
    if details is None:
        return "unknown"
    reason = getattr(details, "reason", None)
    if isinstance(reason, str) and reason:
        return reason
    if isinstance(details, dict):
        value = details.get("reason")
        if isinstance(value, str) and value:
            return value
    return "unknown"


def _strip_fence(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
