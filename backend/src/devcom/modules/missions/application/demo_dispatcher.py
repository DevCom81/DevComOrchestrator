from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from devcom.modules.missions.domain.dispatch_proposal import (
    AuthorizationBlockProposal,
    ClarifyProposal,
    DispatchProposal,
    RouteProposal,
)
from devcom.modules.missions.domain.mission import (
    ClarificationChoice,
    ClarificationQuestion,
)

RuleDict = dict[str, Any]


@dataclass(frozen=True, slots=True)
class DemoDispatchRules:
    version: int
    mode: str
    disclaimer: str
    rules: tuple[RuleDict, ...]


class DemoDispatcher:
    """Deterministic demo router — not natural-language understanding."""

    def __init__(self, rules: DemoDispatchRules) -> None:
        self._rules = rules

    @property
    def meta(self) -> DemoDispatchRules:
        return self._rules

    def propose(self, request_text: str) -> DispatchProposal:
        normalized = _normalize(request_text)
        fallback: RuleDict | None = None
        candidates: list[tuple[int, RuleDict]] = []
        for rule in self._rules.rules:
            match = rule.get("match", {})
            if match.get("fallback"):
                fallback = rule
                continue
            if _matches(normalized, rule):
                candidates.append((int(rule.get("priority", 100)), rule))
        if not candidates:
            return self._clarify_from(fallback)
        candidates.sort(key=lambda item: item[0])
        if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
            return self._clarify_from(fallback)
        return self._to_proposal(candidates[0][1])

    def propose_from_rule(self, rule_id: str) -> DispatchProposal:
        for rule in self._rules.rules:
            if rule["id"] == rule_id and not rule.get("match", {}).get("fallback"):
                return self._to_proposal(rule)
        return self._clarify_from(self._fallback_rule())

    def _fallback_rule(self) -> RuleDict | None:
        for rule in self._rules.rules:
            if rule.get("match", {}).get("fallback"):
                return rule
        return None

    def _clarify_from(self, rule: RuleDict | None) -> ClarifyProposal:
        if rule is None:
            return ClarifyProposal(
                rule_id="builtin_unknown",
                questions=(),
                rationale="Demande non reconnue par le routage de démonstration.",
            )
        proposal = self._to_proposal(rule)
        if isinstance(proposal, ClarifyProposal):
            return proposal
        return ClarifyProposal(
            rule_id=rule["id"],
            questions=(),
            rationale="Demande non reconnue par le routage de démonstration.",
        )

    def _to_proposal(self, rule: RuleDict) -> DispatchProposal:
        outcome = rule["outcome"]
        outcome_type = outcome["type"]
        if outcome_type == "route":
            return RouteProposal(
                rule_id=rule["id"],
                capability_ids=tuple(outcome["capability_ids"]),
                rationale=outcome["rationale"],
            )
        if outcome_type == "authorization_block":
            return AuthorizationBlockProposal(
                rule_id=rule["id"],
                action_id=outcome["action_id"],
                message=outcome["message"],
                rationale=outcome["rationale"],
            )
        questions = tuple(
            ClarificationQuestion(
                id=item["id"],
                prompt=item["prompt"],
                choices=tuple(
                    ClarificationChoice(
                        id=choice["id"],
                        label=choice["label"],
                        maps_to_rule=choice["maps_to_rule"],
                    )
                    for choice in item["choices"]
                ),
            )
            for item in outcome["questions"]
        )
        return ClarifyProposal(
            rule_id=rule["id"],
            questions=questions,
            rationale="Demande non reconnue ou ambiguë — clarification requise.",
        )


def _normalize(text: str) -> str:
    lowered = text.casefold()
    return re.sub(r"\s+", " ", lowered).strip()


def _matches(normalized: str, rule: RuleDict) -> bool:
    match = rule.get("match", {})
    for phrase in rule.get("negative_phrases", []):
        if _normalize(phrase) in normalized:
            return False
    all_phrases = match.get("all_phrases")
    if all_phrases is not None:
        return all(_normalize(phrase) in normalized for phrase in all_phrases)
    groups = match.get("all_groups")
    if groups is not None:
        return all(
            any(_normalize(token) in normalized for token in group) for group in groups
        )
    return False
