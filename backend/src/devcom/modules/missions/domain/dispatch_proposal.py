from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.domain.mission import ClarificationQuestion


@dataclass(frozen=True, slots=True)
class RouteProposal:
    rule_id: str
    capability_ids: tuple[str, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class ClarifyProposal:
    rule_id: str
    questions: tuple[ClarificationQuestion, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class AuthorizationBlockProposal:
    rule_id: str
    action_id: str
    message: str
    rationale: str


DispatchProposal = RouteProposal | ClarifyProposal | AuthorizationBlockProposal
