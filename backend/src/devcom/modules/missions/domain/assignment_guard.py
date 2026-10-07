from __future__ import annotations

from uuid import uuid4

from devcom.modules.missions.domain.capability import CapabilityRegistry
from devcom.modules.missions.domain.errors import OutOfScopeAssignmentError
from devcom.modules.missions.domain.mission import TaskAssignment
from devcom.modules.missions.domain.mission_status import TaskAssignmentStatus


def assign_agent(
    registry: CapabilityRegistry,
    capability_id: str,
    agent_id: str,
    rationale: str,
) -> TaskAssignment:
    capability = registry.get(capability_id)
    if capability is None:
        raise OutOfScopeAssignmentError(f"unknown capability `{capability_id}`")
    if not capability.allows(agent_id):
        raise OutOfScopeAssignmentError(
            f"agent `{agent_id}` cannot receive capability `{capability_id}`"
        )
    return TaskAssignment(
        id=str(uuid4()),
        capability_id=capability_id,
        agent_id=agent_id,
        status=TaskAssignmentStatus.VALIDATED,
        rationale=rationale,
    )


def pick_allowed_agent(registry: CapabilityRegistry, capability_id: str) -> str:
    capability = registry.get(capability_id)
    if capability is None or not capability.allowed_agents:
        raise OutOfScopeAssignmentError(f"no agent available for `{capability_id}`")
    return sorted(capability.allowed_agents)[0]
