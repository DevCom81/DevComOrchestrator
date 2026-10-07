from pathlib import Path

from devcom.modules.missions.adapters.json_contracts import load_demo_dispatch_rules
from devcom.modules.missions.application.demo_dispatcher import DemoDispatcher
from devcom.modules.missions.domain.dispatch_proposal import (
    AuthorizationBlockProposal,
    ClarifyProposal,
    RouteProposal,
)

REPO = Path(__file__).resolve().parents[3]


def _dispatcher() -> DemoDispatcher:
    path = REPO / "contracts" / "dispatch" / "demo_rules.json"
    return DemoDispatcher(load_demo_dispatch_rules(path))


def test_mail_route() -> None:
    proposal = _dispatcher().propose("Classer ces mails")
    assert isinstance(proposal, RouteProposal)
    assert proposal.capability_ids == ("mail.classify",)


def test_sqlite_two_capabilities() -> None:
    proposal = _dispatcher().propose("Concevoir la persistance SQLite")
    assert isinstance(proposal, RouteProposal)
    assert proposal.capability_ids == (
        "data.sqlite_design",
        "arch.persistence_boundaries",
    )


def test_external_block() -> None:
    proposal = _dispatcher().propose("Envoyer ce mail au client")
    assert isinstance(proposal, AuthorizationBlockProposal)
    assert proposal.action_id == "mail.send"


def test_negative_phrase_does_not_route_mail() -> None:
    proposal = _dispatcher().propose("Ne pas classer les mails aujourd'hui")
    assert isinstance(proposal, ClarifyProposal)


def test_quoted_or_negated_sqlite() -> None:
    proposal = _dispatcher().propose('On a dit "pas de sqlite" dans le compte-rendu')
    assert isinstance(proposal, ClarifyProposal)


def test_unknown_asks_clarification() -> None:
    proposal = _dispatcher().propose("Optimiser la stratégie globale de l'univers")
    assert isinstance(proposal, ClarifyProposal)
    assert proposal.questions
