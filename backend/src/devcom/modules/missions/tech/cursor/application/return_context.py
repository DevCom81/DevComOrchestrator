from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from devcom.modules.missions.tech.cursor.adapters.return_artifacts import (
    CursorReturnArtifactStore,
)
from devcom.modules.missions.tech.cursor.adapters.sqlalchemy_cursor_store import (
    SqlAlchemyCursorStore,
)
from devcom.modules.missions.tech.cursor.domain.errors import CursorNotFoundError


@dataclass(frozen=True, slots=True)
class GetReturnContextQuery:
    return_id: str


class GetReturnContext:
    """Immutable analysis context: real report+diff bytes + fingerprints + refs."""

    def __init__(
        self,
        plans: SqlAlchemyCursorStore,
        artifacts: CursorReturnArtifactStore,
    ) -> None:
        self._plans = plans
        self._artifacts = artifacts

    def execute(self, query: GetReturnContextQuery) -> dict[str, Any]:
        item = self._plans.get_return(query.return_id)
        if item is None:
            raise CursorNotFoundError("cursor return not found")
        plan = self._plans.get_plan(item["plan_id"])
        export_id = item.get("export_id")
        content_hash = plan.content_hash if plan is not None else ""
        plan_version = plan.plan_version if plan is not None else 0
        if export_id:
            export = self._plans.get_export(export_id)
            if export is None:
                raise CursorNotFoundError("export not found")
            content_hash = export["content_hash"]
            plan_version = export["plan_version"]
        report = self._artifacts.read_text(item["artifact_dir"], "report.txt")
        diff = self._artifacts.read_text(item["artifact_dir"], "diff.patch")
        return {
            "return_id": item["id"],
            "plan_id": item["plan_id"],
            "export_id": export_id,
            "execution_id": item.get("execution_id"),
            "export_content_hash": content_hash,
            "export_plan_version": plan_version,
            "code_snapshot_id": None if plan is None else plan.code_snapshot_id,
            "report_sha256": item["report_sha256"],
            "diff_sha256": item["diff_sha256"],
            "report_bytes": item["report_bytes"],
            "diff_bytes": item["diff_bytes"],
            "verification_status": item["verification_status"],
            "verification_notes": item["verification_notes"],
            "declared_base": item["declared_base"],
            "declared_commit": item["declared_commit"],
            "report_text": report,
            "diff_text": diff,
            "warning": (
                "Contexte non fiable — déclarations de tests/application "
                "Cursor ne constituent pas des preuves. "
                "Commande/exit/logs = preuves d'exécution des validations."
            ),
        }
