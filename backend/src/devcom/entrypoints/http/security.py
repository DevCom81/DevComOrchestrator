from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from devcom.bootstrap.settings import Settings

MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class LocalMutationGuard(BaseHTTPMiddleware):
    """Validate Host and Origin on mutating API requests."""

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        if not path.startswith("/api/") or request.method not in MUTATING_METHODS:
            return await call_next(request)

        host = (request.headers.get("host") or "").lower()
        if host not in self._settings.allowed_host_list:
            return _reject("invalid_host", "Host header is not allowed", 403)

        origin = request.headers.get("origin")
        if origin is None:
            # Same-origin browser navigations omit Origin; still require JSON mutations.
            pass
        elif origin not in self._settings.mutation_origin_list:
            return _reject("invalid_origin", "Origin is not allowed for mutations", 403)

        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            return _reject(
                "invalid_content_type",
                "Mutations require Content-Type: application/json",
                415,
            )

        return await call_next(request)


def _reject(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message},
    )
