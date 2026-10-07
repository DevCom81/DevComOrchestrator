from __future__ import annotations

import json
from typing import Any

from devcom.modules.missions.tech.domain.artifacts import (
    Challenge,
    ContextSnapshot,
    Disagreement,
    Finding,
    Proposal,
    SpecialistAnalysis,
    Synthesis,
)
from devcom.modules.missions.tech.domain.status import EffortBand, RiskLevel


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(raw: str | None) -> Any:
    if raw is None:
        return None
    return json.loads(raw)


def snapshot_to_dict(snapshot: ContextSnapshot) -> dict[str, object]:
    return {
        "project_id": snapshot.project_id,
        "project_name": snapshot.project_name,
        "project_description": snapshot.project_description,
        "project_updated_at": snapshot.project_updated_at,
        "captured_at": snapshot.captured_at,
        "code_snapshot_id": snapshot.code_snapshot_id,
        "has_code_sources": snapshot.has_code_sources,
    }


def snapshot_from_dict(data: dict[str, object]) -> ContextSnapshot:
    return ContextSnapshot(
        project_id=str(data["project_id"]),
        project_name=str(data["project_name"]),
        project_description=str(data["project_description"]),
        project_updated_at=str(data["project_updated_at"]),
        captured_at=str(data["captured_at"]),
        code_snapshot_id=(
            None if data.get("code_snapshot_id") in (None, "") else str(data["code_snapshot_id"])
        ),
        has_code_sources=bool(data.get("has_code_sources", False)),
    )


def analyses_to_json(analyses: list[SpecialistAnalysis]) -> str:
    return dumps(
        [
            {
                "agent_id": item.agent_id,
                "capability_id": item.capability_id,
                "findings": [_finding_dict(finding) for finding in item.findings],
                "unknowns": list(item.unknowns),
                "out_of_scope_findings": list(item.out_of_scope_findings),
            }
            for item in analyses
        ]
    )


def analyses_from_json(raw: str | None) -> list[SpecialistAnalysis]:
    payload = loads(raw) or []
    return [
        SpecialistAnalysis(
            agent_id=item["agent_id"],
            capability_id=item["capability_id"],
            findings=tuple(_finding_obj(finding) for finding in item["findings"]),
            unknowns=tuple(item.get("unknowns", [])),
            out_of_scope_findings=tuple(item.get("out_of_scope_findings", [])),
        )
        for item in payload
    ]


def challenges_to_json(challenges: list[Challenge]) -> str:
    return dumps(
        [
            {
                "id": item.id,
                "challenger_agent_id": item.challenger_agent_id,
                "target_finding_id": item.target_finding_id,
                "objection": item.objection,
                "evidence_refs": list(item.evidence_refs),
                "author_response": item.author_response,
                "domain": item.domain,
            }
            for item in challenges
        ]
    )


def challenges_from_json(raw: str | None) -> list[Challenge]:
    payload = loads(raw) or []
    return [
        Challenge(
            id=item["id"],
            challenger_agent_id=item["challenger_agent_id"],
            target_finding_id=item["target_finding_id"],
            objection=item["objection"],
            evidence_refs=tuple(item.get("evidence_refs", [])),
            author_response=item["author_response"],
            domain=item["domain"],
        )
        for item in payload
    ]


def synthesis_to_json(synthesis: Synthesis | None) -> str | None:
    if synthesis is None:
        return None
    return dumps(
        {
            "summary": synthesis.summary,
            "evidence_refs": list(synthesis.evidence_refs),
            "disagreements": [
                {
                    "id": item.id,
                    "summary": item.summary,
                    "related_finding_ids": list(item.related_finding_ids),
                    "related_challenge_ids": list(item.related_challenge_ids),
                }
                for item in synthesis.disagreements
            ],
        }
    )


def synthesis_from_json(raw: str | None) -> Synthesis | None:
    data = loads(raw)
    if data is None:
        return None
    return Synthesis(
        summary=data["summary"],
        evidence_refs=tuple(data.get("evidence_refs", [])),
        disagreements=tuple(
            Disagreement(
                id=item["id"],
                summary=item["summary"],
                related_finding_ids=tuple(item.get("related_finding_ids", [])),
                related_challenge_ids=tuple(item.get("related_challenge_ids", [])),
            )
            for item in data.get("disagreements", [])
        ),
    )


def proposals_to_json(proposals: list[Proposal]) -> str:
    return dumps(
        [
            {
                "id": item.id,
                "title": item.title,
                "solution": item.solution,
                "advantages": list(item.advantages),
                "risks": list(item.risks),
                "tradeoffs": list(item.tradeoffs),
                "validations": list(item.validations),
                "effort": item.effort.value,
                "related_finding_ids": list(item.related_finding_ids),
                "accepts_finding_ids": list(item.accepts_finding_ids),
                "blocked": item.blocked,
                "block_reason": item.block_reason,
                "lift_conditions": list(item.lift_conditions),
            }
            for item in proposals
        ]
    )


def proposals_from_json(raw: str | None) -> list[Proposal]:
    payload = loads(raw) or []
    return [
        Proposal(
            id=item["id"],
            title=item["title"],
            solution=item["solution"],
            advantages=tuple(item.get("advantages", [])),
            risks=tuple(item.get("risks", [])),
            tradeoffs=tuple(item.get("tradeoffs", [])),
            validations=tuple(item.get("validations", [])),
            effort=EffortBand(item["effort"]),
            related_finding_ids=tuple(item.get("related_finding_ids", [])),
            accepts_finding_ids=tuple(item.get("accepts_finding_ids", [])),
            blocked=bool(item.get("blocked", False)),
            block_reason=item.get("block_reason"),
            lift_conditions=tuple(item.get("lift_conditions", [])),
        )
        for item in payload
    ]


def _finding_dict(finding: Finding) -> dict[str, object]:
    return {
        "id": finding.id,
        "domain": finding.domain,
        "observation": finding.observation,
        "evidence_refs": list(finding.evidence_refs),
        "risk_level": finding.risk_level.value,
        "recommendation": finding.recommendation,
        "hypotheses": list(finding.hypotheses),
    }


def _finding_obj(raw: dict[str, Any]) -> Finding:
    return Finding(
        id=raw["id"],
        domain=raw["domain"],
        observation=raw["observation"],
        evidence_refs=tuple(raw.get("evidence_refs", [])),
        risk_level=RiskLevel(raw["risk_level"]),
        recommendation=raw["recommendation"],
        hypotheses=tuple(raw.get("hypotheses", [])),
    )
