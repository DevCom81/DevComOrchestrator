from __future__ import annotations

import json
from pathlib import Path

from devcom.modules.agents.domain.agent_identity import AgentIdentity


class StaticAgentCatalog:
    def __init__(self, contracts_dir: Path) -> None:
        self._contracts_dir = contracts_dir

    def list(self) -> list[AgentIdentity]:
        path = self._contracts_dir / "catalogue.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        agents: list[AgentIdentity] = []
        for item in payload["agents"]:
            bullets = item["specialty_bullets"]
            if len(bullets) != 3:
                raise ValueError(f"agent {item['id']} must declare exactly 3 specialty bullets")
            agents.append(
                AgentIdentity(
                    id=item["id"],
                    display_name=item["display_name"],
                    specialty_bullets=(bullets[0], bullets[1], bullets[2]),
                )
            )
        return agents
