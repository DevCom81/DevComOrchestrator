from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from devcom.bootstrap.composition import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    container = request.app.state.container
    if not isinstance(container, ApplicationContainer):
        raise RuntimeError("application container is not configured")
    return container


ContainerDep = Annotated[ApplicationContainer, Depends(get_container)]
