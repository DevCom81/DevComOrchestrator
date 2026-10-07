from __future__ import annotations

import json
from typing import Any

from devcom.modules.missions.tech.ports.llm_completion import (
    LlmRequest,
    LlmResult,
    LlmUsage,
)


class FakeLlmAdapter:
    """Deterministic double — never touches the network."""

    def __init__(self, scripted: dict[str, dict[str, Any]] | None = None) -> None:
        self._scripted = scripted or {}
        self.calls: list[str] = []

    def complete(self, request: LlmRequest) -> LlmResult:
        self.calls.append(request.step_key)
        scripted = self._scripted.get(request.step_key)
        if scripted is not None:
            return LlmResult(
                ok=bool(scripted.get("ok", True)),
                parsed=scripted.get("parsed"),
                usage=LlmUsage(
                    input_tokens=int(scripted.get("input_tokens", 100)),
                    output_tokens=int(scripted.get("output_tokens", 50)),
                    reasoning_tokens=int(scripted.get("reasoning_tokens", 0)),
                ),
                error_code=scripted.get("error_code"),
                error_message=scripted.get("error_message"),
                provider_refusal=bool(scripted.get("provider_refusal", False)),
            )
        return LlmResult(
            ok=True,
            parsed=_default_payload(request),
            usage=LlmUsage(input_tokens=120, output_tokens=80, reasoning_tokens=0),
            error_code=None,
            error_message=None,
        )

    def count_input_tokens(self, request: LlmRequest) -> tuple[int | None, str]:
        raw = (
            request.system_prompt
            + json.dumps(request.user_payload, ensure_ascii=False)
            + json.dumps(request.json_schema, ensure_ascii=False)
        )
        return max(1, len(raw) // 4), "fake_char_div4"


def _default_payload(request: LlmRequest) -> dict[str, Any]:
    if request.step_key.startswith("analyze:"):
        return {
            "findings": [
                {
                    "id": f"f-{request.agent_id}-1",
                    "domain": request.agent_id,
                    "observation": f"Observation {request.agent_id}",
                    "evidence_refs": ["snapshot:project"],
                    "risk_level": "low",
                    "recommendation": "Conserver le périmètre.",
                    "hypotheses": [],
                }
            ],
            "unknowns": [],
            "out_of_scope_findings": [],
        }
    if request.step_key.startswith("critique:"):
        return {
            "has_objection": False,
            "objection": "",
            "target_finding_id": "",
            "evidence_refs": [],
        }
    if request.step_key.startswith("reply:"):
        return {"author_response": "Accord.", "evidence_refs": ["snapshot:project"]}
    return _synthesize_default(request)


def _synthesize_default(request: LlmRequest) -> dict[str, Any]:
    finding_ids: list[str] = []
    for analysis in request.user_payload.get("analyses", []):
        for finding in analysis.get("findings", []):
            finding_ids.append(finding["id"])
    related = finding_ids[:3] if finding_ids else ["f-missing"]
    return {
        "summary": "Synthèse fake assemblant les avis spécialisés.",
        "disagreements": [],
        "proposals": [
            {
                "id": "p-fake-a",
                "title": "Option A",
                "solution": "Solution A",
                "advantages": ["simple"],
                "risks": ["limité"],
                "tradeoffs": ["scope"],
                "validations": ["tests"],
                "effort": "S",
                "related_finding_ids": related,
                "accepts_finding_ids": [],
            }
        ],
    }
