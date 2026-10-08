from __future__ import annotations

from typing import Any

from devcom.entrypoints.http.schemas.cursor_schemas import (
    ApprovalDto,
    CursorExportDto,
    CursorPlanDto,
    CursorReturnDto,
    ReturnContextDto,
)
from devcom.modules.approvals.domain.approval import ApprovalRequest
from devcom.modules.missions.tech.cursor.domain.plan import CursorPlan


def plan_to_dto(plan: CursorPlan) -> CursorPlanDto:
    return CursorPlanDto(
        id=plan.id,
        project_id=plan.project_id,
        review_id=plan.review_id,
        proposal_id=plan.proposal_id,
        proposal_version=plan.proposal_version,
        adr_id=plan.adr_id,
        code_snapshot_id=plan.code_snapshot_id,
        status=plan.status.value,
        plan_version=plan.plan_version,
        objectif=plan.objectif,
        perimetre=plan.perimetre,
        exclusions=plan.exclusions,
        contraintes_architecture=plan.contraintes_architecture,
        criteres_acceptation=plan.criteres_acceptation,
        validations_attendues=plan.validations_attendues,
        content_hash=plan.content_hash,
        canon_version=plan.canon_version,
        active_approval_id=plan.active_approval_id,
        preview_text=plan.preview_text(),
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def approval_to_dto(item: ApprovalRequest) -> ApprovalDto:
    return ApprovalDto(
        id=item.id,
        action_id=item.action_id,
        target_id=item.target_id,
        payload_hash=item.payload_hash,
        resource_version=item.resource_version,
        status=item.status.value,
        author=item.author,
        created_at=item.created_at,
        expires_at=item.expires_at,
        decided_at=item.decided_at,
        consumed_at=item.consumed_at,
    )


def export_to_dto(item: dict[str, Any]) -> CursorExportDto:
    markdown = item["markdown_utf8"].decode("utf-8")
    return CursorExportDto(
        id=item["id"],
        plan_id=item["plan_id"],
        plan_version=item["plan_version"],
        content_hash=item["content_hash"],
        approval_id=item["approval_id"],
        manifest_json=item["manifest_json"],
        created_at=item["created_at"],
        download_markdown=markdown,
    )


def return_to_dto(item: dict[str, Any]) -> CursorReturnDto:
    return CursorReturnDto(
        id=item["id"],
        plan_id=item["plan_id"],
        export_id=item["export_id"],
        project_id=item["project_id"],
        report_sha256=item["report_sha256"],
        diff_sha256=item["diff_sha256"],
        report_bytes=item["report_bytes"],
        diff_bytes=item["diff_bytes"],
        declared_base=item["declared_base"],
        declared_commit=item["declared_commit"],
        verification_status=item["verification_status"],
        verification_notes=item["verification_notes"],
        linked_review_id=item["linked_review_id"],
        imported_at=item["imported_at"],
    )


def context_to_dto(item: dict[str, Any]) -> ReturnContextDto:
    return ReturnContextDto(**item)
