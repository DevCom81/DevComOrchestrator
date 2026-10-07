from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from devcom.modules.missions.domain.errors import PermissionDeniedError, UnknownActionError


class PermissionEffect(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_AUTHORIZATION = "require_authorization"


class PermissionClass(StrEnum):
    READ = "READ"
    PROPOSE = "PROPOSE"
    MODIFY = "MODIFY"
    EXTERNAL = "EXTERNAL"


@dataclass(frozen=True, slots=True)
class PermissionAction:
    id: str
    effect: PermissionEffect
    permission_class: PermissionClass
    description: str


@dataclass(frozen=True, slots=True)
class PermissionPolicy:
    version: int
    default_effect: PermissionEffect
    tools_enabled: bool
    actions: dict[str, PermissionAction]

    def evaluate(self, action_id: str) -> PermissionAction:
        action = self.actions.get(action_id)
        if action is None:
            if self.default_effect == PermissionEffect.DENY:
                raise UnknownActionError(f"unknown action `{action_id}` denied by default")
            raise PermissionDeniedError(f"action `{action_id}` is not allowed")
        if action.effect == PermissionEffect.DENY:
            raise PermissionDeniedError(f"action `{action_id}` is denied by policy")
        return action
