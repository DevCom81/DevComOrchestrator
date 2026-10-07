from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text

from devcom.bootstrap.app_factory import create_app
from devcom.bootstrap.composition import build_container
from devcom.bootstrap.settings import Settings
from devcom.modules.billing.adapters import sqlalchemy_models as _billing  # noqa: F401
from devcom.modules.missions.adapters import sqlalchemy_models as _missions  # noqa: F401
from devcom.modules.missions.tech.adapters import sqlalchemy_models as _tech  # noqa: F401
from devcom.modules.projects.adapters import code_context_models as _code_ctx  # noqa: F401
from devcom.modules.projects.adapters import sqlalchemy_models as _projects  # noqa: F401
from devcom.shared.persistence import Base

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        mode="demo",
        host="127.0.0.1",
        port=8765,
        data_dir=tmp_path / "data",
        cors_origins="http://127.0.0.1:5173,http://localhost:5173",
        allowed_hosts="127.0.0.1:8765,localhost:8765,testserver",
        contracts_root=REPO_ROOT / "contracts",
        frontend_dist=tmp_path / "missing-dist",
    )


@pytest.fixture()
def migrated_settings(settings: Settings) -> Settings:
    settings.ensure_data_dir()
    engine = create_engine(
        f"sqlite:///{settings.database_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection: object, _record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1
    engine.dispose()
    return settings


@pytest.fixture()
def client(migrated_settings: Settings) -> Iterator[TestClient]:
    container = build_container(migrated_settings)
    app = create_app(settings=migrated_settings, container=container)
    with TestClient(app, base_url="http://127.0.0.1:8765") as test_client:
        yield test_client
