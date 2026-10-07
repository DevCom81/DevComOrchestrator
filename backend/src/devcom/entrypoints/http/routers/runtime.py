from fastapi import APIRouter

from devcom.entrypoints.http.deps import ContainerDep
from devcom.entrypoints.http.schemas.runtime_schemas import RuntimeDto

router = APIRouter(tags=["runtime"])


@router.get("/api/runtime", response_model=RuntimeDto)
def runtime(container: ContainerDep) -> RuntimeDto:
    settings = container.settings
    return RuntimeDto(
        mode=settings.mode,
        app_name=settings.app_name,
        version=settings.version,
    )
