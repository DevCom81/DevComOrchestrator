from __future__ import annotations

from typing import Protocol

from devcom.modules.agents.domain.agent_identity import AgentIdentity


class AgentCatalog(Protocol):
    def list(self) -> list[AgentIdentity]:
        """Return the ordered agent catalogue."""


class ListAgents:
    def __init__(self, catalog: AgentCatalog) -> None:
        self._catalog = catalog

    def execute(self) -> list[AgentIdentity]:
        return self._catalog.list()
