from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.application.create_review import (
    CreateTechReview,
    CreateTechReviewCommand,
)
from devcom.modules.missions.tech.application.permissions_guard import require_tech_action
from devcom.modules.missions.tech.cursor.adapters.return_artifacts import (
    CursorReturnArtifactStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorNotFoundError,
)
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import ExecutionMode


@dataclass(frozen=True, slots=True)
class CreateReturnTechReviewCommand:
    return_id: str
    idempotency_key: str
    execution_mode: ExecutionMode = ExecutionMode.DEMO


class CreateReturnTechReview:
    """Creates a TechReview linked to immutable return context — no automatic run."""

    def __init__(
        self,
        *,
        plans: SqlAlchemyCursorStore,
        artifacts: CursorReturnArtifactStore,
        create_review: CreateTechReview,
        policy: PermissionPolicy,
    ) -> None:
        self._plans = plans
        self._artifacts = artifacts
        self._create = create_review
        self._policy = policy

    def execute(self, command: CreateReturnTechReviewCommand) -> TechReview:
        require_tech_action(self._policy, "tech.review.create")
        item = self._plans.get_return(command.return_id)
        if item is None:
            raise CursorNotFoundError("cursor return not found")
        if item["linked_review_id"]:
            raise CursorConflictError("return already linked to a tech review")
        plan = self._plans.get_plan(item["plan_id"])
        if plan is None:
            raise CursorNotFoundError("cursor plan not found")
        export_id = item.get("export_id")
        execution_id = item.get("execution_id")
        if export_id:
            export = self._plans.get_export(export_id)
            if export is None:
                raise CursorNotFoundError("export not found")
            export_ref = f"export_id={export['id']} export_hash={export['content_hash']}"
        elif execution_id:
            export_ref = f"execution_id={execution_id} plan_hash={plan.content_hash}"
        else:
            raise CursorConflictError("return missing export_id and execution_id")
        # Ensure payload files exist (immutable context material).
        _ = self._artifacts.read_text(item["artifact_dir"], "report.txt")
        _ = self._artifacts.read_text(item["artifact_dir"], "diff.patch")
        request = (
            f"Revue du retour Cursor return_id={item['id']} "
            f"{export_ref} "
            f"report_sha={item['report_sha256']} diff_sha={item['diff_sha256']} "
            f"verification={item['verification_status']}. "
            "Le contexte immuable (rapport+diff) est attaché au retour ; "
            "les déclarations de tests Cursor ne sont pas des preuves. "
            "Lancement IA explicite avec budget — aucun coût sur GET. "
            "Prévisualiser le contexte avant tout lancement."
        )
        review = self._create.execute(
            CreateTechReviewCommand(
                project_id=item["project_id"],
                request_text=request[:2000],
                idempotency_key=command.idempotency_key,
                execution_mode=command.execution_mode,
                code_snapshot_id=plan.code_snapshot_id,
            )
        )
        self._plans.set_return_linked_review(item["id"], review.id)
        return review
