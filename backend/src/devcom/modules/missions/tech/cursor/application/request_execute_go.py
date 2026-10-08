from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from devcom.modules.approvals.adapters.sqlalchemy_store import SqlAlchemyApprovalStore
from devcom.modules.approvals.domain.approval import ApprovalRequest
from devcom.modules.approvals.domain.status import ACTION_CURSOR_EXECUTE
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.git_workspace import require_clean_git_base
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_execution_store import (
    SqlAlchemyExecutionStore,
)
from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorNotFoundError,
    CursorValidationError,
)
from devcom.modules.missions.tech.cursor.domain.execute_canon import (
    build_execute_payload,
    execute_payload_hash,
)
from devcom.modules.missions.tech.cursor.domain.execution_status import (
    DEFAULT_CURSOR_FAST,
    DEFAULT_CURSOR_MODEL,
    EXECUTE_RESERVE_EUR_MICROS,
    MAX_CORRECTIONS_PER_PLAN_VERSION,
    SANDBOX_POLICY_VERSION,
)
from devcom.modules.missions.tech.cursor.domain.plan import CursorPlan
from devcom.shared.time import Clock


@dataclass(frozen=True, slots=True)
class RequestExecuteGoCommand:
    plan_id: str
    expected_version: int
    idempotency_key: str
    source_root: str
    correction: bool = False
    prior_execution_id: str | None = None
    review_observations: str = ""


class RequestExecuteGo:
    def __init__(
        self,
        *,
        plans: SqlAlchemyCursorStore,
        executions: SqlAlchemyExecutionStore,
        approvals: SqlAlchemyApprovalStore,
        policy: PermissionPolicy,
        clock: Clock,
    ) -> None:
        self._plans = plans
        self._executions = executions
        self._approvals = approvals
        self._policy = policy
        self._clock = clock

    def execute(
        self, command: RequestExecuteGoCommand
    ) -> tuple[dict[str, object], ApprovalRequest]:
        require_tech_action(self._policy, "cursor.execution.request_go")
        if not command.idempotency_key.strip():
            raise CursorValidationError("idempotency key required")
        plan = self._plans.get_plan(command.plan_id)
        if plan is None:
            raise CursorNotFoundError("cursor plan not found")
        existing = self._approvals.get_by_idempotency(command.idempotency_key)
        preview = self._preview(command, plan)
        if existing is not None:
            return preview, existing
        plan.expect_version(command.expected_version)
        now = self._clock.now()
        self._approvals.invalidate_open_for_target(
            target_id=plan.id,
            action_id=ACTION_CURSOR_EXECUTE,
            now=now,
        )
        approval = ApprovalRequest.create(
            action_id=ACTION_CURSOR_EXECUTE,
            target_id=plan.id,
            payload_hash=str(preview["payload_hash"]),
            resource_version=plan.plan_version,
            now=now,
            idempotency_key=command.idempotency_key,
        )
        self._approvals.save(approval)
        return preview, approval

    def _preview(
        self, command: RequestExecuteGoCommand, plan: CursorPlan
    ) -> dict[str, object]:
        root = Path(command.source_root)
        commit = require_clean_git_base(root)
        correction_index = 0
        prior_sha = None
        parent_id = None
        observations = ""
        if command.correction:
            if plan.corrections_used >= MAX_CORRECTIONS_PER_PLAN_VERSION:
                raise CursorConflictError("correction limit reached for this plan version")
            if not command.prior_execution_id:
                raise CursorValidationError("prior_execution_id required for correction")
            prior = self._executions.get(command.prior_execution_id)
            if prior is None or prior.plan_id != plan.id:
                raise CursorNotFoundError("prior execution not found")
            if not prior.capture_manifest_sha:
                raise CursorConflictError("prior execution has no capture")
            correction_index = plan.corrections_used + 1
            prior_sha = prior.capture_manifest_sha
            parent_id = prior.id
            observations = command.review_observations.strip()
            if not observations:
                raise CursorValidationError("review_observations required for correction")
        validations = [
            line.strip() for line in plan.validations_attendues.splitlines() if line.strip()
        ]
        payload = build_execute_payload(
            plan_id=plan.id,
            plan_version=plan.plan_version,
            content_hash=plan.content_hash,
            project_id=plan.project_id,
            source_root=str(root.resolve()),
            git_base_commit=commit,
            model_id=DEFAULT_CURSOR_MODEL,
            model_fast=DEFAULT_CURSOR_FAST,
            sandbox_policy_version=SANDBOX_POLICY_VERSION,
            validation_commands=validations,
            reserved_eur_micros=EXECUTE_RESERVE_EUR_MICROS,
            correction_index=correction_index,
            prior_execution_id=parent_id,
            review_observations=observations,
            prior_capture_sha=prior_sha,
        )
        digest = execute_payload_hash(payload)
        return {
            "payload": payload,
            "payload_hash": digest,
            "payload_json": json.dumps(payload, ensure_ascii=False, sort_keys=True),
            "budget_layers": {
                "devcom_reservation_eur_micros": EXECUTE_RESERVE_EUR_MICROS,
                "cursor_cost": "unknown_until_run",
                "provider_guarantee": "account_side_only_not_app_enforced",
            },
        }
