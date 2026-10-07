from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Capability:
    id: str
    domain: str
    task_type: str
    allowed_agents: frozenset[str]
    excluded_agents: frozenset[str]
    description: str

    def allows(self, agent_id: str) -> bool:
        if agent_id in self.excluded_agents:
            return False
        return agent_id in self.allowed_agents


@dataclass(frozen=True, slots=True)
class CapabilityRegistry:
    version: int
    tools_enabled: bool
    capabilities: dict[str, Capability]

    def get(self, capability_id: str) -> Capability | None:
        return self.capabilities.get(capability_id)

    def capabilities_for_agent(self, agent_id: str) -> tuple[str, ...]:
        return tuple(
            capability.id
            for capability in self.capabilities.values()
            if capability.allows(agent_id)
        )
