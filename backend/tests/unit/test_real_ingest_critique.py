from __future__ import annotations

from devcom.modules.missions.tech.application.real_ingest import ingest_critique
from devcom.modules.missions.tech.domain.artifacts import Finding
from devcom.modules.missions.tech.domain.status import RiskLevel


def _finding() -> Finding:
    return Finding(
        id="f-cyber-1",
        domain="cyber",
        observation="obs",
        evidence_refs=("snapshot:project",),
        risk_level=RiskLevel.LOW,
        recommendation="ok",
        hypotheses=(),
    )


def test_ingest_critique_skips_when_has_objection_false() -> None:
    findings = {"f-cyber-1": _finding()}
    challenges: list = []
    ok = ingest_critique(
        {"agent_id": "cyber"},
        {
            "has_objection": False,
            "objection": "",
            "target_finding_id": "",
            "evidence_refs": [],
        },
        findings,
        challenges,
        {"snapshot:project", "f-cyber-1"},
    )
    assert ok
    assert challenges == []


def test_ingest_critique_records_one_objection() -> None:
    findings = {"f-cyber-1": _finding()}
    challenges: list = []
    ok = ingest_critique(
        {"agent_id": "qa"},
        {
            "has_objection": True,
            "objection": "Preuve insuffisante.",
            "target_finding_id": "f-cyber-1",
            "evidence_refs": ["snapshot:project"],
        },
        findings,
        challenges,
        {"snapshot:project", "f-cyber-1"},
    )
    assert ok
    assert len(challenges) == 1
    assert challenges[0].objection == "Preuve insuffisante."
