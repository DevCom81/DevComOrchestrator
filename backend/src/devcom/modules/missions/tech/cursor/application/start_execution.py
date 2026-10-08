from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devcom.modules.approvals.adapters.sqlalchemy_store import SqlAlchemyApprovalStore
from devcom.modules.approvals.domain.approval import ApprovalRequest
from devcom.modules.approvals.domain.errors import ApprovalNotFoundError
from devcom.modules.approvals.domain.status import ACTION_CURSOR_EXECUTE
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.execution_budget import (
    ExecutionBudgetGate,
)
from devcom.modules.missions.tech.cursor.adapters.git_workspace import (
    prepare_execution_worktree,
)
from devcom.modules.missions.tech.cursor.adapters.return_artifacts import (
    CursorReturnArtifactStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_execution_store import (
    SqlAlchemyExecutionStore,
)
from devcom.modules.missions.tech.cursor.application.execution_capture_step import (
    build_execute_prompt,
    capture_and_attach_return,
    map_provider_status,
)
from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorNotFoundError,
    CursorValidationError,
)
from devcom.modules.missions.tech.cursor.domain.execution import CursorExecution
from devcom.modules.missions.tech.cursor.domain.execution_status import ExecutionStatus
from devcom.modules.missions.tech.cursor.domain.plan import CursorPlan
from devcom.modules.missions.tech.cursor.ports.cursor_agent_port import (
    AgentInvokeResult,
    CursorAgentPort,
)
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class StartExecutionCommand:
    plan_id: str
    approval_id: str
    idempotency_key: str
    payload_json: str
    payload_hash: str


class StartExecution:
    def __init__(
        self,
        *,
        plans: SqlAlchemyCursorStore,
        executions: SqlAlchemyExecutionStore,
        approvals: SqlAlchemyApprovalStore,
        agent: CursorAgentPort,
        budget: ExecutionBudgetGate,
        artifacts: CursorReturnArtifactStore,
        runs_root: Path,
        policy: PermissionPolicy,
        clock: Clock,
    ) -> None:
        self._plans = plans
        self._executions = executions
        self._approvals = approvals
        self._agent = agent
        self._budget = budget
        self._artifacts = artifacts
        self._runs_root = runs_root
        self._policy = policy
        self._clock = clock

    def execute(self, command: StartExecutionCommand) -> CursorExecution:
        require_tech_action(self._policy, "cursor.execution.start")
        existing = self._executions.get_by_idempotency(command.idempotency_key)
        if existing is not None:
            return existing
        plan = self._plans.get_plan(command.plan_id)
        if plan is None:
            raise CursorNotFoundError("cursor plan not found")
        approval = self._require_execute_approval(command, plan)
        intent = self._persist_intent(command, plan, approval)
        return self._invoke_and_capture(intent, plan_markdown=plan.preview_text())

    def _require_execute_approval(
        self, command: StartExecutionCommand, plan: CursorPlan
    ) -> ApprovalRequest:
        approval = self._approvals.get(command.approval_id)
        if approval is None:
            raise ApprovalNotFoundError("approval not found")
        if approval.action_id != ACTION_CURSOR_EXECUTE:
            raise CursorConflictError("approval is not an execute GO")
        if command.payload_hash != approval.payload_hash:
            raise CursorConflictError("payload hash mismatch vs GO")
        now = self._clock.now()
        approval.consume_granted(
            payload_hash=command.payload_hash,
            resource_version=plan.plan_version,
            now=now,
        )
        self._approvals.save(approval)
        return approval

    def _persist_intent(
        self,
        command: StartExecutionCommand,
        plan: CursorPlan,
        approval: ApprovalRequest,
    ) -> CursorExecution:
        payload: dict[str, Any] = json.loads(command.payload_json)
        correction_index = int(payload.get("correction_index") or 0)
        if correction_index > 0:
            plan.register_correction()
            self._plans.save_plan(plan)
        prior = payload.get("prior_execution_id")
        now = self._clock.now()
        intent = CursorExecution.create_intent(
            project_id=plan.project_id,
            plan_id=plan.id,
            plan_version=plan.plan_version,
            content_hash=plan.content_hash,
            correction_index=correction_index,
            parent_execution_id=str(prior) if prior else None,
            execute_payload_hash=command.payload_hash,
            execute_payload_json=command.payload_json,
            approval_id=approval.id,
            idempotency_key=command.idempotency_key,
            source_root=str(payload["source_root"]),
            git_base_commit=str(payload["git_base_commit"]),
            model_id=str(payload["model_id"]),
            model_fast=str(payload["model_fast"]),
            sandbox_policy_version=str(payload["sandbox_policy_version"]),
            reserved_eur_micros=int(payload["reserved_eur_micros"]),
            now=now,
        )
        self._executions.save(intent)
        self._budget.reserve(
            execution_id=intent.id,
            eur_micros=intent.reserved_eur_micros,
            now=now,
        )
        return intent

    def _invoke_and_capture(
        self, intent: CursorExecution, *, plan_markdown: str
    ) -> CursorExecution:
        work = self._prepare_worktree(intent)
        intent.mark_running(worktree=str(work), now=self._clock.now())
        self._executions.save(intent)
        prompt = build_execute_prompt(plan_markdown, intent.execute_payload_json)
        try:
            result = self._agent.invoke_once(
                worktree=work,
                prompt=prompt,
                model_id=intent.model_id,
                model_fast=intent.model_fast,
            )
        except (CursorConflictError, CursorValidationError, OSError, RuntimeError) as exc:
            return self._handle_invoke_failure(intent, exc)
        return self._finalize_success(intent, work, result)

    def _prepare_worktree(self, intent: CursorExecution) -> Path:
        work = self._runs_root / intent.id / "worktree"
        try:
            prepare_execution_worktree(
                source_root=Path(intent.source_root),
                dest=work,
                base_commit=intent.git_base_commit,
            )
        except (CursorConflictError, CursorValidationError, OSError) as exc:
            intent.confirm_terminal(
                status=ExecutionStatus.FAILED,
                writes_stable=True,
                now=self._clock.now(),
                error_message=str(exc),
            )
            self._executions.save(intent)
            self._budget.release_unused(execution_id=intent.id)
            raise
        return work

    def _handle_invoke_failure(
        self, intent: CursorExecution, exc: Exception
    ) -> CursorExecution:
        status = self._agent.try_reconnect(
            agent_id=intent.agent_id or "",
            run_id=intent.run_id or "",
        )
        terminal = (
            ExecutionStatus.UNCERTAIN if status is None else ExecutionStatus.INTERRUPTED
        )
        intent.confirm_terminal(
            status=terminal,
            writes_stable=False,
            now=self._clock.now(),
            error_message=str(exc),
        )
        self._executions.save(intent)
        self._budget.mark_uncertain(execution_id=intent.id)
        return intent

    def _finalize_success(
        self,
        intent: CursorExecution,
        work: Path,
        result: AgentInvokeResult,
    ) -> CursorExecution:
        intent.attach_agent(
            agent_id=result.agent_id, run_id=result.run_id, now=self._clock.now()
        )
        intent.usage_json = json.dumps(result.usage) if result.usage else None
        intent.billed_json = json.dumps(result.billed) if result.billed else None
        mapped = map_provider_status(result.status, intent.cancel_requested)
        intent.confirm_terminal(
            status=mapped,
            writes_stable=result.writes_stable,
            now=self._clock.now(),
            error_message=result.billed_error,
        )
        self._executions.save(intent)
        if not result.writes_stable:
            intent.mark_capture(
                manifest_sha="incomplete",
                incomplete=True,
                now=self._clock.now(),
            )
            self._executions.save(intent)
            self._budget.mark_uncertain(execution_id=intent.id)
            return intent
        return capture_and_attach_return(
            intent=intent,
            work=work,
            runs_root=self._runs_root,
            plans=self._plans,
            executions=self._executions,
            artifacts=self._artifacts,
            budget=self._budget,
            clock=self._clock,
        )
