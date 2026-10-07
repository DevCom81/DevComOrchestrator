from __future__ import annotations

import json
from pathlib import Path

from devcom.modules.missions.application.demo_dispatcher import DemoDispatchRules
from devcom.modules.missions.domain.capability import Capability, CapabilityRegistry
from devcom.modules.missions.domain.permission import (
    PermissionAction,
    PermissionClass,
    PermissionEffect,
    PermissionPolicy,
)


def load_capability_registry(path: Path) -> CapabilityRegistry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    capabilities = {
        item["id"]: Capability(
            id=item["id"],
            domain=item["domain"],
            task_type=item["task_type"],
            allowed_agents=frozenset(item["allowed_agents"]),
            excluded_agents=frozenset(item["excluded_agents"]),
            description=item["description"],
        )
        for item in payload["capabilities"]
    }
    return CapabilityRegistry(
        version=int(payload["version"]),
        tools_enabled=bool(payload["tools_enabled"]),
        capabilities=capabilities,
    )


def load_permission_policy(path: Path) -> PermissionPolicy:
    payload = json.loads(path.read_text(encoding="utf-8"))
    actions = {
        item["id"]: PermissionAction(
            id=item["id"],
            effect=PermissionEffect(item["effect"]),
            permission_class=PermissionClass(item["permission_class"]),
            description=item["description"],
        )
        for item in payload["actions"]
    }
    return PermissionPolicy(
        version=int(payload["version"]),
        default_effect=PermissionEffect(payload["default_effect"]),
        tools_enabled=bool(payload["tools_enabled"]),
        actions=actions,
    )


def load_demo_dispatch_rules(path: Path) -> DemoDispatchRules:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return DemoDispatchRules(
        version=int(payload["version"]),
        mode=payload["mode"],
        disclaimer=payload["disclaimer"],
        rules=tuple(payload["rules"]),
    )
