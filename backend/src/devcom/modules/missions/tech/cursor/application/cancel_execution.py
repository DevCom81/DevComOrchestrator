from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_execution_store import (
    SqlAlchemyExecutionStore,
)
from devcom.modules.missions.tech.cursor.domain.errors import CursorNotFoundError
from devcom.modules.missions.tech.cursor.domain.execution import CursorExecution
from devcom.modules.missions.tech.cursor.domain.execution_status import ExecutionStatus
from devcom.modules.missions.tech.cursor.ports.cursor_agent_port import CursorAgentPort
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class CancelExecutionCommand:
    execution_id: str


class CancelExecution:
    def __init__(
        self,
        *,
        executions: SqlAlchemyExecutionStore,
        agent: CursorAgentPort,
        policy: PermissionPolicy,
        clock: Clock,
    ) -> None:
        self._executions = executions
        self._agent = agent
        self._policy = policy
        self._clock = clock

    def execute(self, command: CancelExecutionCommand) -> CursorExecution:
        require_tech_action(self._policy, "cursor.execution.cancel")
        item = self._executions.get(command.execution_id)
        if item is None:
            raise CursorNotFoundError("execution not found")
        now = self._clock.now()
        item.request_cancel(now)
        self._executions.save(item)
        confirmed = False
        if item.agent_id and item.run_id:
            confirmed = self._agent.cancel(agent_id=item.agent_id, run_id=item.run_id)
        if confirmed:
            item.confirm_terminal(
                status=ExecutionStatus.CANCELLED,
                writes_stable=False,
                now=self._clock.now(),
                error_message="cancel requested and acknowledged by runtime",
            )
        else:
            item.error_message = "cancel requested — stop not yet confirmed"
            item.updated_at = self._clock.now()
        self._executions.save(item)
        return item
