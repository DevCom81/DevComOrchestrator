from __future__ import annotations

from typing import Any

from devcom.modules.missions.tech.application.code_sources import sources_payload
from devcom.modules.missions.tech.application.prompt_loader import PromptBundle
from devcom.modules.missions.tech.application.real_ingest import (
    analysis_dict,
    author_of,
    finding_dict,
)
from devcom.modules.missions.tech.domain.artifacts import (
    Challenge,
    Finding,
    SpecialistAnalysis,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.ports.llm_completion import LlmRequest
from devcom.modules.projects.domain.code_artifacts import CodeSnapshot

LlmParts = tuple[str, dict[str, Any], dict[str, Any]]


def build_llm_request(
    *,
    review: TechReview,
    step: dict[str, Any],
    prompts: PromptBundle,
    analyses: dict[str, SpecialistAnalysis],
    findings: dict[str, Finding],
    challenges: list[Challenge],
    code_snapshot: CodeSnapshot | None = None,
) -> LlmRequest:
    phase = step["phase"]
    if phase == "analyze":
        system, schema, payload = _analyze_parts(review, step, prompts, code_snapshot)
    elif phase == "critique":
        system, schema, payload = _critique_parts(step, prompts, findings)
    elif phase == "reply":
        system, schema, payload = _reply_parts(step, prompts, analyses, findings, challenges)
    else:
        system, schema, payload = _synthesize_parts(prompts, analyses, challenges)
    return LlmRequest(
        step_key=step["step_key"],
        agent_id=step["agent_id"],
        capability_id=step["capability_id"],
        model_id=step["model_id"],
        effort=step["effort"],
        system_prompt=system,
        user_payload=payload,
        json_schema=schema,
        max_output_tokens=step["max_output"],
        max_input_tokens=step["max_input"],
    )


def _analyze_parts(
    review: TechReview,
    step: dict[str, Any],
    prompts: PromptBundle,
    code_snapshot: CodeSnapshot | None,
) -> LlmParts:
    system = prompts.system(
        "specialist_analyze_v1.md",
        agent_id=step["agent_id"],
        capability_id=step["capability_id"],
    )
    snapshot = review.snapshot
    payload = {
        "request_text": review.request_text,
        "snapshot": {
            "project_id": snapshot.project_id if snapshot else "",
            "project_name": snapshot.project_name if snapshot else "",
            "project_description": snapshot.project_description if snapshot else "",
            "project_updated_at": snapshot.project_updated_at if snapshot else "",
            "captured_at": snapshot.captured_at if snapshot else "",
            "code_snapshot_id": snapshot.code_snapshot_id if snapshot else None,
            "has_code_sources": snapshot.has_code_sources if snapshot else False,
        },
        "sources": sources_payload(code_snapshot),
    }
    return system, prompts.schema("analyze.json"), payload


def _critique_parts(
    step: dict[str, Any],
    prompts: PromptBundle,
    findings: dict[str, Finding],
) -> LlmParts:
    system = prompts.system("specialist_critique_v1.md", agent_id=step["agent_id"])
    payload = {"findings": [finding_dict(item) for item in findings.values()]}
    return system, prompts.schema("critique.json"), payload


def _reply_parts(
    step: dict[str, Any],
    prompts: PromptBundle,
    analyses: dict[str, SpecialistAnalysis],
    findings: dict[str, Finding],
    challenges: list[Challenge],
) -> LlmParts:
    system = prompts.system("specialist_reply_v1.md", agent_id=step["agent_id"])
    payload = {
        "challenges": [
            {
                "id": item.id,
                "challenger_agent_id": item.challenger_agent_id,
                "target_finding_id": item.target_finding_id,
                "objection": item.objection,
                "evidence_refs": list(item.evidence_refs),
                "domain": item.domain,
            }
            for item in challenges
            if item.target_finding_id in findings
            and author_of(findings[item.target_finding_id], analyses) == step["agent_id"]
        ]
    }
    return system, prompts.schema("reply.json"), payload


def _synthesize_parts(
    prompts: PromptBundle,
    analyses: dict[str, SpecialistAnalysis],
    challenges: list[Challenge],
) -> LlmParts:
    system = prompts.system("synthesize_v1.md")
    payload = {
        "analyses": [analysis_dict(item) for item in analyses.values()],
        "challenges": [
            {
                "id": item.id,
                "challenger_agent_id": item.challenger_agent_id,
                "target_finding_id": item.target_finding_id,
                "objection": item.objection,
                "author_response": item.author_response,
                "evidence_refs": list(item.evidence_refs),
                "domain": item.domain,
            }
            for item in challenges
        ],
    }
    return system, prompts.schema("synthesize.json"), payload
