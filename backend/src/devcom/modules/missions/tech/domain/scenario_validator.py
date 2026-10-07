from __future__ import annotations

from typing import Any

from devcom.modules.missions.domain.assignment_guard import assign_agent
from devcom.modules.missions.domain.capability import CapabilityRegistry
from devcom.modules.missions.domain.errors import OutOfScopeAssignmentError
from devcom.modules.missions.tech.domain.errors import ScenarioContractError

REQUIRED_AGENTS = (
    "architecte",
    "cyber",
    "qa",
    "devops",
    "fullstack",
    "sql_data",
)


def validate_scenario_contract(
    payload: dict[str, Any],
    registry: CapabilityRegistry,
) -> None:
    specialists = payload.get("specialists")
    if not isinstance(specialists, list) or len(specialists) != 6:
        raise ScenarioContractError("scenario must declare exactly 6 specialists")
    agent_ids = [item.get("agent_id") for item in specialists]
    if sorted(agent_ids) != sorted(REQUIRED_AGENTS):
        raise ScenarioContractError("scenario specialists must be the six TECH agents")
    finding_ids: set[str] = set()
    for item in specialists:
        capability_id = item["capability_id"]
        agent_id = item["agent_id"]
        try:
            assign_agent(registry, capability_id, agent_id, "scenario-contract")
        except OutOfScopeAssignmentError as exc:
            raise ScenarioContractError(str(exc)) from exc
        for finding in item.get("findings", []):
            finding_ids.add(finding["id"])
    _validate_refs(payload, finding_ids)


def _validate_refs(payload: dict[str, Any], finding_ids: set[str]) -> None:
    challenge_ids: set[str] = set()
    for challenge in payload.get("challenges", []):
        challenge_ids.add(challenge["id"])
        if challenge["target_finding_id"] not in finding_ids:
            raise ScenarioContractError(
                f"challenge `{challenge['id']}` references unknown finding"
            )
        if challenge["challenger_agent_id"] not in REQUIRED_AGENTS:
            raise ScenarioContractError("challenge challenger out of TECH set")
    for disagreement in payload.get("disagreements", []):
        for finding_id in disagreement.get("related_finding_ids", []):
            if finding_id not in finding_ids:
                raise ScenarioContractError("disagreement references unknown finding")
        for challenge_id in disagreement.get("related_challenge_ids", []):
            if challenge_id not in challenge_ids:
                raise ScenarioContractError("disagreement references unknown challenge")
    for proposal in payload.get("proposals", []):
        for finding_id in proposal.get("related_finding_ids", []):
            if finding_id not in finding_ids:
                raise ScenarioContractError("proposal references unknown finding")
        for finding_id in proposal.get("accepts_finding_ids", []):
            if finding_id not in finding_ids:
                raise ScenarioContractError("proposal accepts unknown finding")
    if not payload.get("proposals"):
        raise ScenarioContractError("scenario must declare at least one proposal")
