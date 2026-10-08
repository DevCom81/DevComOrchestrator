from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from devcom.modules.missions.tech.cursor.domain import package_canon as canon
from devcom.modules.missions.tech.cursor.domain.errors import (
    CursorConflictError,
    CursorValidationError,
)
from devcom.modules.missions.tech.cursor.domain.status import CANON_VERSION, CursorPlanStatus


@dataclass(slots=True)
class CursorPlan:
    id: str
    project_id: str
    review_id: str
    proposal_id: str
    proposal_version: int
    adr_id: str
    code_snapshot_id: str | None
    status: CursorPlanStatus
    plan_version: int
    objectif: str
    perimetre: str
    exclusions: str
    contraintes_architecture: str
    criteres_acceptation: str
    validations_attendues: str
    markdown_utf8: bytes
    metadata_json: str
    content_hash: str
    canon_version: str
    active_approval_id: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        review_id: str,
        proposal_id: str,
        proposal_version: int,
        adr_id: str,
        code_snapshot_id: str | None,
        sections: dict[str, str],
        now: datetime,
    ) -> CursorPlan:
        stamp = _utc(now)
        markdown = canon.build_markdown(sections)
        markdown_utf8 = canon.normalize_markdown(markdown)
        meta = _base_meta(
            project_id=project_id,
            review_id=review_id,
            proposal_id=proposal_id,
            proposal_version=proposal_version,
            adr_id=adr_id,
            code_snapshot_id=code_snapshot_id,
            plan_version=1,
        )
        content_hash = canon.compute_content_hash(markdown_utf8, meta)
        return cls(
            id=str(uuid4()),
            project_id=project_id,
            review_id=review_id,
            proposal_id=proposal_id,
            proposal_version=proposal_version,
            adr_id=adr_id,
            code_snapshot_id=code_snapshot_id,
            status=CursorPlanStatus.DRAFT,
            plan_version=1,
            objectif=sections["objectif"].strip(),
            perimetre=sections["perimetre"].strip(),
            exclusions=sections["exclusions"].strip(),
            contraintes_architecture=sections["contraintes_architecture"].strip(),
            criteres_acceptation=sections["criteres_acceptation"].strip(),
            validations_attendues=sections["validations_attendues"].strip(),
            markdown_utf8=markdown_utf8,
            metadata_json=canon.manifest_json(canon.metadata_without_hash(meta)),
            content_hash=content_hash,
            canon_version=CANON_VERSION,
            active_approval_id=None,
            created_at=stamp,
            updated_at=stamp,
        )

    def update_sections(self, sections: dict[str, str], *, now: datetime) -> None:
        if self.status == CursorPlanStatus.EXPORTED and self.active_approval_id:
            pass
        markdown = canon.build_markdown(sections)
        markdown_utf8 = canon.normalize_markdown(markdown)
        self.plan_version += 1
        self.objectif = sections["objectif"].strip()
        self.perimetre = sections["perimetre"].strip()
        self.exclusions = sections["exclusions"].strip()
        self.contraintes_architecture = sections["contraintes_architecture"].strip()
        self.criteres_acceptation = sections["criteres_acceptation"].strip()
        self.validations_attendues = sections["validations_attendues"].strip()
        self.markdown_utf8 = markdown_utf8
        meta = _base_meta(
            project_id=self.project_id,
            review_id=self.review_id,
            proposal_id=self.proposal_id,
            proposal_version=self.proposal_version,
            adr_id=self.adr_id,
            code_snapshot_id=self.code_snapshot_id,
            plan_version=self.plan_version,
        )
        self.content_hash = canon.compute_content_hash(markdown_utf8, meta)
        self.metadata_json = canon.manifest_json(canon.metadata_without_hash(meta))
        self.status = CursorPlanStatus.DRAFT
        self.active_approval_id = None
        self.updated_at = _utc(now)

    def expect_version(self, expected: int) -> None:
        if expected != self.plan_version:
            raise CursorConflictError("stale plan version — reload and retry")

    def mark_awaiting_go(self, approval_id: str, now: datetime) -> None:
        self.status = CursorPlanStatus.AWAITING_GO
        self.active_approval_id = approval_id
        self.updated_at = _utc(now)

    def mark_go_granted(self, now: datetime) -> None:
        self.status = CursorPlanStatus.GO_GRANTED
        self.updated_at = _utc(now)

    def mark_exported(self, now: datetime) -> None:
        self.status = CursorPlanStatus.EXPORTED
        self.updated_at = _utc(now)

    def mark_return_imported(self, now: datetime) -> None:
        self.status = CursorPlanStatus.RETURN_IMPORTED
        self.updated_at = _utc(now)

    def approved_manifest(self) -> dict[str, Any]:
        import json

        meta = json.loads(self.metadata_json)
        return canon.build_manifest(meta, self.content_hash)

    def preview_text(self) -> str:
        return canon.preview_document(self.markdown_utf8, self.approved_manifest())


def _base_meta(
    *,
    project_id: str,
    review_id: str,
    proposal_id: str,
    proposal_version: int,
    adr_id: str,
    code_snapshot_id: str | None,
    plan_version: int,
) -> dict[str, Any]:
    return {
        "adr_id": adr_id,
        "code_snapshot_id": code_snapshot_id,
        "plan_version": plan_version,
        "project_id": project_id,
        "proposal_id": proposal_id,
        "proposal_version": proposal_version,
        "review_id": review_id,
    }


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise CursorValidationError("timestamps must be timezone-aware UTC")
    return value.astimezone(UTC)
