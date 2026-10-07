from __future__ import annotations

from typing import Any

from devcom.modules.missions.tech.domain.artifacts import (
    Challenge,
    Finding,
    SpecialistAnalysis,
)
from devcom.modules.missions.tech.domain.status import RiskLevel


def needs_reply(
    agent_id: str,
    challenges: list[Challenge],
    analyses: dict[str, SpecialistAnalysis],
    findings: dict[str, Finding],
) -> bool:
    return any(
        author_of(findings[item.target_finding_id], analyses) == agent_id
        for item in challenges
        if item.target_finding_id in findings
    )


def author_of(finding: Finding, analyses: dict[str, SpecialistAnalysis]) -> str | None:
    for analysis in analyses.values():
        if any(item.id == finding.id for item in analysis.findings):
            return analysis.agent_id
    return None


def finding_dict(finding: Finding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "domain": finding.domain,
        "observation": finding.observation,
        "evidence_refs": list(finding.evidence_refs),
        "risk_level": finding.risk_level.value,
        "recommendation": finding.recommendation,
        "hypotheses": list(finding.hypotheses),
    }


def analysis_dict(analysis: SpecialistAnalysis) -> dict[str, Any]:
    return {
        "agent_id": analysis.agent_id,
        "capability_id": analysis.capability_id,
        "findings": [finding_dict(item) for item in analysis.findings],
        "unknowns": list(analysis.unknowns),
        "out_of_scope_findings": list(analysis.out_of_scope_findings),
    }


def ingest_analysis(
    step: dict[str, Any],
    parsed: dict[str, Any],
    analyses: dict[str, SpecialistAnalysis],
    findings: dict[str, Finding],
    allowed_refs: set[str],
) -> bool:
    parsed_findings: list[Finding] = []
    for raw in parsed.get("findings", []):
        refs = tuple(raw.get("evidence_refs", []))
        for ref in refs:
            if ref in allowed_refs:
                continue
            return False
        finding = Finding(
            id=raw["id"],
            domain=raw["domain"],
            observation=raw["observation"],
            evidence_refs=refs,
            risk_level=RiskLevel(raw["risk_level"]),
            recommendation=raw["recommendation"],
            hypotheses=tuple(raw.get("hypotheses", [])),
        )
        findings[finding.id] = finding
        parsed_findings.append(finding)
        allowed_refs.add(finding.id)
    analyses[step["agent_id"]] = SpecialistAnalysis(
        agent_id=step["agent_id"],
        capability_id=step["capability_id"],
        findings=tuple(parsed_findings),
        unknowns=tuple(parsed.get("unknowns", [])),
        out_of_scope_findings=tuple(parsed.get("out_of_scope_findings", [])),
    )
    return True


def ingest_critique(
    step: dict[str, Any],
    parsed: dict[str, Any],
    findings: dict[str, Finding],
    challenges: list[Challenge],
    allowed_refs: set[str],
) -> bool:
    if not _critique_has_objection(parsed):
        return True
    objection = parsed.get("objection")
    target = parsed.get("target_finding_id")
    if not isinstance(objection, str) or not objection.strip():
        return False
    if not isinstance(target, str) or target not in findings:
        return False
    for ref in parsed.get("evidence_refs", []):
        if ref not in allowed_refs and ref not in findings:
            return False
    challenges.append(
        Challenge(
            id=f"c-{step['agent_id']}-{target}",
            challenger_agent_id=step["agent_id"],
            target_finding_id=target,
            objection=objection.strip(),
            evidence_refs=tuple(parsed.get("evidence_refs", [])),
            author_response="",
            domain=findings[target].domain,
        )
    )
    return True


def _critique_has_objection(parsed: dict[str, Any]) -> bool:
    flag = parsed.get("has_objection")
    if isinstance(flag, bool):
        return flag
    objection = parsed.get("objection")
    if objection is None:
        return False
    if isinstance(objection, str):
        return bool(objection.strip())
    return False


def ingest_reply(
    step: dict[str, Any],
    parsed: dict[str, Any],
    analyses: dict[str, SpecialistAnalysis],
    findings: dict[str, Finding],
    challenges: list[Challenge],
) -> bool:
    response = parsed.get("author_response")
    if not isinstance(response, str) or not response.strip():
        return False
    updated = False
    for index, challenge in enumerate(challenges):
        finding = findings.get(challenge.target_finding_id)
        if finding is None:
            continue
        if author_of(finding, analyses) != step["agent_id"]:
            continue
        challenges[index] = Challenge(
            id=challenge.id,
            challenger_agent_id=challenge.challenger_agent_id,
            target_finding_id=challenge.target_finding_id,
            objection=challenge.objection,
            evidence_refs=challenge.evidence_refs,
            author_response=response.strip(),
            domain=challenge.domain,
        )
        updated = True
    return updated
