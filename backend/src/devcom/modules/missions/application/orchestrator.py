from __future__ import annotations

from datetime import datetime

from devcom.modules.missions.application.demo_dispatcher import DemoDispatcher, DemoDispatchRules
from devcom.modules.missions.domain.assignment_guard import assign_agent, pick_allowed_agent
from devcom.modules.missions.domain.capability import CapabilityRegistry
from devcom.modules.missions.domain.dispatch_proposal import (
    AuthorizationBlockProposal,
    ClarifyProposal,
    DispatchProposal,
    RouteProposal,
)
from devcom.modules.missions.domain.errors import OutOfScopeAssignmentError
from devcom.modules.missions.domain.mission import (
    AuthorizationBlock,
    Mission,
    RoutingRecord,
)
from devcom.modules.missions.domain.permission import PermissionEffect, PermissionPolicy


class MissionOrchestrator:
    def __init__(
        self,
        dispatcher: DemoDispatcher,
        registry: CapabilityRegistry,
        policy: PermissionPolicy,
    ) -> None:
        self._dispatcher = dispatcher
        self._registry = registry
        self._policy = policy

    def route_text(self, mission: Mission, request_text: str, now: datetime) -> None:
        self.apply_proposal(mission, self._dispatcher.propose(request_text), now)

    def route_from_rule(self, mission: Mission, rule_id: str, now: datetime) -> None:
        self.apply_proposal(mission, self._dispatcher.propose_from_rule(rule_id), now)

    def apply_proposal(
        self,
        mission: Mission,
        proposal: DispatchProposal,
        now: datetime,
    ) -> None:
        meta = self._dispatcher.meta
        if isinstance(proposal, RouteProposal):
            self._apply_route(mission, proposal, meta, now)
            return
        if isinstance(proposal, AuthorizationBlockProposal):
            self._apply_block(mission, proposal, meta, now)
            return
        self._apply_clarify(mission, proposal, meta, now)

    def _apply_route(
        self,
        mission: Mission,
        proposal: RouteProposal,
        meta: DemoDispatchRules,
        now: datetime,
    ) -> None:
        self._policy.evaluate("mission.route")
        tasks = [
            assign_agent(
                self._registry,
                capability_id,
                pick_allowed_agent(self._registry, capability_id),
                proposal.rationale,
            )
            for capability_id in proposal.capability_ids
        ]
        routing = _routing(
            meta,
            proposal.rule_id,
            proposal.rationale,
            self._registry,
            self._policy,
        )
        mission.apply_routed(routing=routing, tasks=tasks, now=now)

    def _apply_block(
        self,
        mission: Mission,
        proposal: AuthorizationBlockProposal,
        meta: DemoDispatchRules,
        now: datetime,
    ) -> None:
        action = self._policy.evaluate(proposal.action_id)
        if action.effect != PermissionEffect.REQUIRE_AUTHORIZATION:
            raise OutOfScopeAssignmentError("external action is not authorization-gated")
        routing = _routing(
            meta,
            proposal.rule_id,
            proposal.rationale,
            self._registry,
            self._policy,
        )
        mission.apply_authorization_block(
            routing=routing,
            block=AuthorizationBlock(
                action_id=proposal.action_id,
                message=proposal.message,
                rationale=proposal.rationale,
            ),
            now=now,
        )

    def _apply_clarify(
        self,
        mission: Mission,
        proposal: ClarifyProposal,
        meta: DemoDispatchRules,
        now: datetime,
    ) -> None:
        self._policy.evaluate("mission.clarify")
        routing = _routing(
            meta,
            proposal.rule_id,
            proposal.rationale,
            self._registry,
            self._policy,
        )
        mission.apply_clarification(
            routing=routing,
            questions=proposal.questions,
            now=now,
        )


def _routing(
    meta: DemoDispatchRules,
    rule_id: str,
    rationale: str,
    registry: CapabilityRegistry,
    policy: PermissionPolicy,
) -> RoutingRecord:
    return RoutingRecord(
        mode=meta.mode,
        disclaimer=meta.disclaimer,
        rule_ids=(rule_id,),
        rationale=rationale,
        capability_registry_version=registry.version,
        permission_policy_version=policy.version,
        dispatch_rules_version=meta.version,
    )
