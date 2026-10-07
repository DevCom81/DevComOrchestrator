from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from devcom.bootstrap.app_factory import create_app
from devcom.bootstrap.composition import build_container
from devcom.bootstrap.settings import Settings
from devcom.modules.projects.adapters.sqlalchemy_models import Base

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
        contracts_dir=REPO_ROOT / "contracts" / "agents",
        frontend_dist=tmp_path / "missing-dist",
    )


@pytest.fixture()
def migrated_settings(settings: Settings) -> Settings:
    settings.ensure_data_dir()
    engine = create_engine(f"sqlite:///{settings.database_path}")
    Base.metadata.create_all(engine)
    engine.dispose()
    return settings


@pytest.fixture()
def client(migrated_settings: Settings) -> Iterator[TestClient]:
    container = build_container(migrated_settings)
    app = create_app(settings=migrated_settings, container=container)
    with TestClient(app, base_url="http://127.0.0.1:8765") as test_client:
        yield test_client
