from __future__ import annotations

import json
from pathlib import Path

from devcom.modules.missions.tech.domain.blocking import BlockingPolicy, BlockingRule
from devcom.modules.missions.tech.domain.status import RiskLevel


def load_blocking_policy(path: Path) -> BlockingPolicy:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = tuple(
        BlockingRule(
            id=item["id"],
            risk_level=RiskLevel(item["when"]["risk_level"]),
            domain=item["when"]["domain"],
            message=item["message"],
            lift_conditions=tuple(item.get("lift_conditions", [])),
        )
        for item in payload["rules"]
    )
    return BlockingPolicy(version=int(payload["version"]), rules=rules)
