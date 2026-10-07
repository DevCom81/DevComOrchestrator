from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from devcom.entrypoints.http.deps import ContainerDep
from devcom.entrypoints.http.schemas.code_context_schemas import (
    AttachSourceRootBody,
    CodePreviewDto,
    CodeSnapshotDto,
    FreezeBody,
    PreviewBody,
    PreviewFileDto,
    SourceRootDto,
    SourceTreeDto,
    TreeEntryDto,
)
from devcom.entrypoints.http.schemas.project_schemas import (
    CreateProjectBody,
    ProjectDto,
    ProjectListDto,
    UpdateProjectBody,
)
from devcom.modules.projects.application.attach_source_root import AttachSourceRootCommand
from devcom.modules.projects.application.browse_source_tree import BrowseSourceTreeQuery
from devcom.modules.projects.application.create_code_preview import CreateCodePreviewCommand
from devcom.modules.projects.application.create_project import CreateProjectCommand
from devcom.modules.projects.application.detach_source_root import DetachSourceRootCommand
from devcom.modules.projects.application.freeze_code_snapshot import FreezeCodeSnapshotCommand
from devcom.modules.projects.application.get_project import GetProjectQuery
from devcom.modules.projects.application.get_source_root import GetSourceRootQuery
from devcom.modules.projects.application.update_project import UpdateProjectCommand
from devcom.modules.projects.domain.code_artifacts import CodePreview, CodeSnapshot
from devcom.modules.projects.domain.project import Project

router = APIRouter(tags=["projects"])


@router.get("/api/projects", response_model=ProjectListDto)
def list_projects(container: ContainerDep) -> ProjectListDto:
    return ProjectListDto(items=[_to_dto(item) for item in container.list_projects.execute()])


@router.post(
    "/api/projects",
    response_model=ProjectDto,
    status_code=status.HTTP_201_CREATED,
)
def create_project(body: CreateProjectBody, container: ContainerDep) -> ProjectDto:
    project = container.create_project.execute(
        CreateProjectCommand(name=body.name, description=body.description)
    )
    return _to_dto(project)


@router.get("/api/projects/{project_id}", response_model=ProjectDto)
def get_project(project_id: str, container: ContainerDep) -> ProjectDto:
    project = container.get_project.execute(GetProjectQuery(project_id=project_id))
    return _to_dto(project)


@router.patch("/api/projects/{project_id}", response_model=ProjectDto)
def update_project(
    project_id: str,
    body: UpdateProjectBody,
    container: ContainerDep,
) -> ProjectDto:
    project = container.update_project.execute(
        UpdateProjectCommand(
            project_id=project_id,
            name=body.name,
            description=body.description,
        )
    )
    return _to_dto(project)


@router.put("/api/projects/{project_id}/source-root", response_model=SourceRootDto)
def attach_source_root(
    project_id: str, body: AttachSourceRootBody, container: ContainerDep
) -> SourceRootDto:
    result = container.attach_source_root.execute(
        AttachSourceRootCommand(
            project_id=project_id,
            absolute_path=body.absolute_path,
            exclusions=tuple(body.exclusions),
        )
    )
    return SourceRootDto(**result)  # type: ignore[arg-type]


@router.delete("/api/projects/{project_id}/source-root", status_code=status.HTTP_204_NO_CONTENT)
def detach_source_root(project_id: str, container: ContainerDep) -> Response:
    container.detach_source_root.execute(DetachSourceRootCommand(project_id=project_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/projects/{project_id}/source-root", response_model=SourceRootDto | None)
def get_source_root(project_id: str, container: ContainerDep) -> SourceRootDto | None:
    result = container.get_source_root.execute(GetSourceRootQuery(project_id=project_id))
    if result is None:
        return None
    return SourceRootDto(**result)  # type: ignore[arg-type]


@router.get("/api/projects/{project_id}/source-tree", response_model=SourceTreeDto)
def browse_source_tree(
    project_id: str,
    container: ContainerDep,
    cursor: str | None = Query(default=None),
) -> SourceTreeDto:
    result = container.browse_source_tree.execute(
        BrowseSourceTreeQuery(project_id=project_id, cursor=cursor)
    )
    raw_entries = result["entries"]
    assert isinstance(raw_entries, list)
    return SourceTreeDto(
        project_id=str(result["project_id"]),
        root_path=str(result["root_path"]),
        entries=[TreeEntryDto(**item) for item in raw_entries],
        cursor=None if result["cursor"] is None else str(result["cursor"]),
        truncated=bool(result["truncated"]),
        limit_message=(
            None if result["limit_message"] is None else str(result["limit_message"])
        ),
        secret_scan_disclaimer=str(result["secret_scan_disclaimer"]),
    )


@router.post(
    "/api/projects/{project_id}/code-context/preview",
    response_model=CodePreviewDto,
    status_code=status.HTTP_201_CREATED,
)
def create_preview(
    project_id: str, body: PreviewBody, container: ContainerDep
) -> CodePreviewDto:
    preview = container.create_code_preview.execute(
        CreateCodePreviewCommand(
            project_id=project_id,
            relative_paths=tuple(body.relative_paths),
        )
    )
    return _preview_dto(preview)


@router.post(
    "/api/projects/{project_id}/code-snapshots",
    response_model=CodeSnapshotDto,
    status_code=status.HTTP_201_CREATED,
)
def freeze_snapshot(
    project_id: str, body: FreezeBody, container: ContainerDep
) -> CodeSnapshotDto:
    snapshot = container.freeze_code_snapshot.execute(
        FreezeCodeSnapshotCommand(project_id=project_id, preview_id=body.preview_id)
    )
    return _snapshot_dto(snapshot)


@router.get(
    "/api/projects/{project_id}/code-snapshots/{snapshot_id}",
    response_model=CodeSnapshotDto,
)
def get_snapshot(
    project_id: str, snapshot_id: str, container: ContainerDep
) -> CodeSnapshotDto:
    snapshot = container.get_code_snapshot.execute(project_id, snapshot_id)
    return _snapshot_dto(snapshot)


def _to_dto(project: Project) -> ProjectDto:
    return ProjectDto(
        id=str(project.id),
        name=project.name.value,
        description=project.description.value,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _preview_dto(preview: CodePreview) -> CodePreviewDto:
    return CodePreviewDto(
        preview_id=preview.id,
        project_id=preview.project_id,
        fingerprint=preview.fingerprint,
        created_at=preview.created_at,
        expires_at=preview.expires_at,
        files=[_file_dto(item) for item in preview.files],
        exclusions=list(preview.exclusions),
        token_upper_bound=preview.token_upper_bound,
        token_indicative=preview.token_indicative,
        token_method_blocking=preview.token_method_blocking,
        token_method_indicative=preview.token_method_indicative,
        reserves_budget=False,
        provider_calls=0,
    )


def _snapshot_dto(snapshot: CodeSnapshot) -> CodeSnapshotDto:
    return CodeSnapshotDto(
        snapshot_id=snapshot.id,
        project_id=snapshot.project_id,
        preview_id=snapshot.preview_id,
        fingerprint=snapshot.fingerprint,
        captured_at=snapshot.captured_at,
        files=[_file_dto(item) for item in snapshot.files],
        exclusions=list(snapshot.exclusions),
        git_commit=snapshot.git.commit,
        git_dirty=snapshot.git.dirty,
        git_note=snapshot.git.note,
        token_upper_bound=snapshot.token_upper_bound,
        token_method_blocking=snapshot.token_method_blocking,
        status=snapshot.status,
    )


def _file_dto(item: object) -> PreviewFileDto:
    from devcom.modules.projects.domain.code_artifacts import FileBlob

    assert isinstance(item, FileBlob)
    return PreviewFileDto(
        relative_path=item.relative_path,
        sha256=item.sha256,
        byte_size=item.byte_size,
        content=item.content_text,
        evidence_ref=f"snapshot:file:{item.relative_path}",
    )
