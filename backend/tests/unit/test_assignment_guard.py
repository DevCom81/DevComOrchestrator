from pathlib import Path

import pytest

from devcom.modules.missions.adapters.json_contracts import load_capability_registry
from devcom.modules.missions.domain.assignment_guard import assign_agent
from devcom.modules.missions.domain.errors import OutOfScopeAssignmentError

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture()
def registry():
    return load_capability_registry(REPO / "contracts" / "capabilities" / "registry.json")


def test_qa_cannot_receive_mail_classify(registry) -> None:
    with pytest.raises(OutOfScopeAssignmentError):
        assign_agent(registry, "mail.classify", "qa", "invalid")


def test_vendeur_cannot_receive_tech_sqlite(registry) -> None:
    with pytest.raises(OutOfScopeAssignmentError):
        assign_agent(registry, "data.sqlite_design", "vendeur", "invalid")


def test_secretaire_can_receive_mail_classify(registry) -> None:
    task = assign_agent(registry, "mail.classify", "secretaire", "ok")
    assert task.agent_id == "secretaire"
