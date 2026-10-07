from __future__ import annotations

from devcom.modules.missions.domain.permission import PermissionEffect, PermissionPolicy
from devcom.modules.missions.tech.domain.errors import TechValidationError


def require_tech_action(policy: PermissionPolicy, action_id: str) -> None:
    action = policy.evaluate(action_id)
    if action.effect != PermissionEffect.ALLOW:
        raise TechValidationError(f"action `{action_id}` is not allowed for demo TECH")
