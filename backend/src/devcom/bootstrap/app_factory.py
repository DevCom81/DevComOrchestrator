from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from devcom.bootstrap.composition import ApplicationContainer, build_container
from devcom.bootstrap.settings import Settings, get_settings
from devcom.entrypoints.http.error_handlers import register_error_handlers
from devcom.entrypoints.http.routers import agents, health, missions, projects, runtime
from devcom.entrypoints.http.security import LocalMutationGuard


def create_app(
    settings: Settings | None = None,
    container: ApplicationContainer | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_container = container or build_container(resolved_settings)

    app = FastAPI(title=resolved_settings.app_name, version=resolved_settings.version)
    app.state.container = resolved_container
    app.state.settings = resolved_settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )
    app.add_middleware(LocalMutationGuard, settings=resolved_settings)
    register_error_handlers(app)

    app.include_router(health.router)
    app.include_router(runtime.router)
    app.include_router(agents.router)
    app.include_router(projects.router)
    app.include_router(missions.router)

    _mount_frontend(app, resolved_settings.frontend_dist)
    return app


def _mount_frontend(app: FastAPI, dist_dir: Path) -> None:
    if not dist_dir.is_dir():
        return
    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    agents_dir = dist_dir / "agents"
    if agents_dir.is_dir():
        app.mount("/agents", StaticFiles(directory=agents_dir), name="agents")

    @app.get("/")
    async def spa_index() -> FileResponse:
        return FileResponse(dist_dir / "index.html")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = dist_dir / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist_dir / "index.html")
