from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.tech.domain.artifacts import Finding, Proposal
from devcom.modules.missions.tech.domain.status import RiskLevel


@dataclass(frozen=True, slots=True)
class BlockingRule:
    id: str
    risk_level: RiskLevel
    domain: str
    message: str
    lift_conditions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BlockingPolicy:
    version: int
    rules: tuple[BlockingRule, ...]


def apply_blocking_policy(
    policy: BlockingPolicy,
    findings: dict[str, Finding],
    proposals: list[Proposal],
) -> list[Proposal]:
    critical_ids = {
        finding_id
        for finding_id, finding in findings.items()
        for rule in policy.rules
        if finding.risk_level == rule.risk_level and finding.domain == rule.domain
    }
    result: list[Proposal] = []
    for proposal in proposals:
        accepted_critical = [
            finding_id
            for finding_id in proposal.accepts_finding_ids
            if finding_id in critical_ids
        ]
        if not accepted_critical:
            result.append(proposal)
            continue
        rule = _matching_rule(policy, findings, accepted_critical)
        result.append(
            Proposal(
                id=proposal.id,
                title=proposal.title,
                solution=proposal.solution,
                advantages=proposal.advantages,
                risks=proposal.risks,
                tradeoffs=proposal.tradeoffs,
                validations=proposal.validations,
                effort=proposal.effort,
                related_finding_ids=proposal.related_finding_ids,
                accepts_finding_ids=proposal.accepts_finding_ids,
                blocked=True,
                block_reason=rule.message,
                lift_conditions=rule.lift_conditions,
            )
        )
    return result


def _matching_rule(
    policy: BlockingPolicy,
    findings: dict[str, Finding],
    accepted_critical: list[str],
) -> BlockingRule:
    for finding_id in accepted_critical:
        finding = findings[finding_id]
        for rule in policy.rules:
            if finding.risk_level == rule.risk_level and finding.domain == rule.domain:
                return rule
    return policy.rules[0]
