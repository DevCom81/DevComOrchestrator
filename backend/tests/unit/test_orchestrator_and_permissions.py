from datetime import UTC, datetime
from pathlib import Path

import pytest

from devcom.modules.missions.adapters.json_contracts import (
    load_capability_registry,
    load_demo_dispatch_rules,
    load_permission_policy,
)
from devcom.modules.missions.application.demo_dispatcher import DemoDispatcher
from devcom.modules.missions.application.orchestrator import MissionOrchestrator
from devcom.modules.missions.domain.dispatch_proposal import RouteProposal
from devcom.modules.missions.domain.errors import (
    OutOfScopeAssignmentError,
    UnknownActionError,
)
from devcom.modules.missions.domain.mission import Mission
from devcom.modules.missions.domain.mission_status import MissionStatus

REPO = Path(__file__).resolve().parents[3]


def _orchestrator() -> MissionOrchestrator:
    dispatch = REPO / "contracts" / "dispatch" / "demo_rules.json"
    registry = REPO / "contracts" / "capabilities" / "registry.json"
    policy = REPO / "contracts" / "permissions" / "policy.json"
    return MissionOrchestrator(
        DemoDispatcher(load_demo_dispatch_rules(dispatch)),
        load_capability_registry(registry),
        load_permission_policy(policy),
    )


def test_invalid_dispatcher_proposal_is_rejected() -> None:
    orchestrator = _orchestrator()
    mission = Mission.create("p1", "Classer ces mails", datetime.now(UTC))
    bad = RouteProposal(
        rule_id="forged",
        capability_ids=("mail.classify",),
        rationale="forged with wrong agent path",
    )
    # Force invalid by monkeypatching pick via unknown capability
    bad_unknown = RouteProposal(
        rule_id="forged",
        capability_ids=("no.such.capability",),
        rationale="invalid",
    )
    with pytest.raises(OutOfScopeAssignmentError):
        orchestrator.apply_proposal(mission, bad_unknown, datetime.now(UTC))
    assert bad.capability_ids == ("mail.classify",)


def test_unknown_action_denied() -> None:
    policy = load_permission_policy(REPO / "contracts" / "permissions" / "policy.json")
    with pytest.raises(UnknownActionError):
        policy.evaluate("totally.unknown.action")


def test_external_blocks_without_tasks() -> None:
    orchestrator = _orchestrator()
    mission = Mission.create("p1", "Envoyer ce mail au client", datetime.now(UTC))
    orchestrator.route_text(mission, mission.request_text, datetime.now(UTC))
    assert mission.status == MissionStatus.BLOCKED_AUTHORIZATION
    assert mission.tasks == []
    assert mission.authorization_block is not None
    assert "préciser" in mission.authorization_block.message
