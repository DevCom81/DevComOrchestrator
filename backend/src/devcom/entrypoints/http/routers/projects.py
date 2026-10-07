from __future__ import annotations

from fastapi import APIRouter, status

from devcom.entrypoints.http.deps import ContainerDep
from devcom.entrypoints.http.schemas.project_schemas import (
    CreateProjectBody,
    ProjectDto,
    ProjectListDto,
    UpdateProjectBody,
)
from devcom.modules.projects.application.create_project import CreateProjectCommand
from devcom.modules.projects.application.get_project import GetProjectQuery
from devcom.modules.projects.application.update_project import UpdateProjectCommand
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


def _to_dto(project: Project) -> ProjectDto:
    return ProjectDto(
        id=str(project.id),
        name=project.name.value,
        description=project.description.value,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
