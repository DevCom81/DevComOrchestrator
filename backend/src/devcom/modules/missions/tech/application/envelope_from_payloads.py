from __future__ import annotations

import json
from typing import Any

from devcom.modules.missions.tech.application.code_sources import sources_payload
from devcom.modules.missions.tech.application.prompt_loader import PromptBundle
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.projects.adapters.token_counter import estimate_tokens
from devcom.modules.projects.domain.code_artifacts import CodeSnapshot

SPECIALISTS = (
    "architecte",
    "cyber",
    "qa",
    "devops",
    "fullstack",
    "sql_data",
)


def input_tokens_by_step(
    *,
    review: TechReview,
    prompts: PromptBundle,
    code: CodeSnapshot | None,
    bounds: dict[str, Any],
) -> dict[str, int]:
    sources = sources_payload(code)
    result: dict[str, int] = {}
    for agent_id in SPECIALISTS:
        result[f"analyze:{agent_id}"] = _count_analyze(
            review, prompts, sources, agent_id, bounds
        )
        critique_key = "critique_architecte" if agent_id == "architecte" else "critique"
        reply_key = "reply_architecte" if agent_id == "architecte" else "reply"
        result[f"critique:{agent_id}"] = _bounded(
            _count_phase(
                prompts,
                "specialist_critique_v1.md",
                "critique.json",
                {"findings": []},
                agent_id,
            ),
            f"critique:{agent_id}",
            int(bounds["token_bounds"][critique_key]["max_input"]),
        )
        result[f"reply:{agent_id}"] = _bounded(
            _count_phase(
                prompts,
                "specialist_reply_v1.md",
                "reply.json",
                {"challenges": [], "author_analysis": {}},
                agent_id,
            ),
            f"reply:{agent_id}",
            int(bounds["token_bounds"][reply_key]["max_input"]),
        )
    result["synthesize"] = _bounded(
        _count_phase(
            prompts,
            "synthesize_v1.md",
            "synthesize.json",
            {"analyses": [], "challenges": []},
            "synthetiseur_tech",
        ),
        "synthesize",
        int(bounds["token_bounds"]["synthesize"]["max_input"]),
    )
    return result


def _bounded(upper: int, step_key: str, max_input: int) -> int:
    if upper > max_input:
        raise ValueError(
            f"{step_key} token upper bound {upper} exceeds max_input {max_input}"
        )
    return upper


def _count_analyze(
    review: TechReview,
    prompts: PromptBundle,
    sources: dict[str, Any],
    agent_id: str,
    bounds: dict[str, Any],
) -> int:
    system = prompts.system(
        "specialist_analyze_v1.md",
        agent_id=agent_id,
        capability_id=f"tech.{agent_id}.analyze",
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
        "sources": sources,
    }
    schema = prompts.schema("analyze.json")
    raw = system + json.dumps(payload, ensure_ascii=False) + json.dumps(schema)
    upper = estimate_tokens(raw).upper_bound
    key = "analyze_architecte" if agent_id == "architecte" else "analyze"
    max_input = int(bounds["token_bounds"][key]["max_input"])
    if upper > max_input:
        raise ValueError(
            f"analyze:{agent_id} token upper bound {upper} exceeds max_input {max_input}"
        )
    return upper


def _count_phase(
    prompts: PromptBundle,
    system_name: str,
    schema_name: str,
    payload: dict[str, Any],
    agent_id: str,
) -> int:
    system = prompts.system(system_name, agent_id=agent_id)
    raw = system + json.dumps(payload, ensure_ascii=False) + json.dumps(prompts.schema(schema_name))
    return estimate_tokens(raw).upper_bound
