from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from devcom.modules.missions.adapters.json_contracts import load_capability_registry
from devcom.modules.missions.tech.adapters.blocking_policy_loader import load_blocking_policy
from devcom.modules.missions.tech.adapters.scenario_catalog import load_scenario_catalog
from devcom.modules.missions.tech.application.pipeline_builder import build_pipeline_results
from devcom.modules.missions.tech.domain.errors import ScenarioContractError
from devcom.modules.missions.tech.domain.scenario_validator import validate_scenario_contract

REPO = Path(__file__).resolve().parents[3]
CONTRACTS = REPO / "contracts"


@pytest.fixture()
def registry():
    return load_capability_registry(CONTRACTS / "capabilities" / "registry.json")


@pytest.fixture()
def blocking():
    return load_blocking_policy(CONTRACTS / "tech" / "blocking_policy.json")


@pytest.fixture()
def catalog():
    return load_scenario_catalog(CONTRACTS / "tech" / "scenarios" / "index.json")


def test_security_scenario_blocks_dangerous_proposal(registry, blocking, catalog) -> None:
    payload = catalog.load_payload("security_critical")
    _analyses, _challenges, synthesis, proposals = build_pipeline_results(
        payload, registry, blocking
    )
    by_id = {item.id: item for item in proposals}
    assert by_id["p-danger"].blocked is True
    assert by_id["p-danger"].block_reason is not None
    assert by_id["p-danger"].lift_conditions
    assert by_id["p-safe"].blocked is False
    assert synthesis.disagreements


def test_local_persistence_keeps_disagreement(registry, blocking, catalog) -> None:
    payload = catalog.load_payload("local_persistence")
    _a, _c, synthesis, proposals = build_pipeline_results(payload, registry, blocking)
    assert len(proposals) == 2
    assert all(not item.blocked for item in proposals)
    assert len(synthesis.disagreements) == 1


def test_invalid_assignment_rejected(registry, catalog) -> None:
    payload = deepcopy(catalog.load_payload("local_persistence"))
    payload["specialists"][0]["agent_id"] = "vendeur"
    with pytest.raises(ScenarioContractError):
        validate_scenario_contract(payload, registry)


def test_broken_reference_rejected(registry, catalog) -> None:
    payload = deepcopy(catalog.load_payload("local_persistence"))
    payload["challenges"][0]["target_finding_id"] = "missing-finding"
    with pytest.raises(ScenarioContractError):
        validate_scenario_contract(payload, registry)
