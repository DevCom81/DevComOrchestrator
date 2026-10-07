from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from devcom.modules.projects.domain.errors import ProjectNotFoundError, ProjectValidationError
from devcom.shared.errors import DomainError, NotFoundError, ValidationError


def _json_error(status_code: int, code: str, message: str, details: object = None) -> JSONResponse:
    payload: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


async def not_found_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, NotFoundError):
        raise exc
    return _json_error(404, exc.code, exc.message)


async def validation_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ValidationError):
        raise exc
    return _json_error(422, exc.code, exc.message)


async def domain_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        raise exc
    return _json_error(400, exc.code, exc.message)


async def request_validation(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    return _json_error(422, "validation_error", "request validation failed", exc.errors())


async def value_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ValueError):
        raise exc
    return _json_error(422, "validation_error", str(exc))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ProjectNotFoundError, not_found_error)
    app.add_exception_handler(NotFoundError, not_found_error)
    app.add_exception_handler(ProjectValidationError, validation_error)
    app.add_exception_handler(ValidationError, validation_error)
    app.add_exception_handler(DomainError, domain_error)
    app.add_exception_handler(RequestValidationError, request_validation)
    app.add_exception_handler(ValueError, value_error)
