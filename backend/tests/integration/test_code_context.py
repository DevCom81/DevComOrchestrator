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
from devcom.modules.projects.adapters import code_context_models as _code  # noqa: F401
from devcom.modules.projects.adapters import sqlalchemy_models as _projects  # noqa: F401
from devcom.shared.persistence import Base

REPO_ROOT = Path(__file__).resolve().parents[3]
ORIGIN = {"Origin": "http://127.0.0.1:5173"}


@pytest.fixture()
def real_settings(tmp_path: Path) -> Settings:
    settings = Settings(
        mode="real",
        llm_adapter="fake",
        cursor_adapter="real",
        cursor_api_key="test-key-not-for-live-calls",
        host="127.0.0.1",
        port=8765,
        data_dir=tmp_path / "data",
        cors_origins="http://127.0.0.1:5173,http://localhost:5173",
        allowed_hosts="127.0.0.1:8765,localhost:8765,testserver",
        contracts_root=REPO_ROOT / "contracts",
        frontend_dist=tmp_path / "missing-dist",
    )
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
def client(real_settings: Settings) -> Iterator[TestClient]:
    container = build_container(real_settings)
    app = create_app(settings=real_settings, container=container)
    with TestClient(app, base_url="http://127.0.0.1:8765") as test_client:
        yield test_client


def _project(client: TestClient) -> str:
    response = client.post(
        "/api/projects",
        json={"name": "Ctx", "description": "Contexte code"},
        headers=ORIGIN,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_preview_freeze_immutable_after_source_change(
    client: TestClient, tmp_path: Path
) -> None:
    project_id = _project(client)
    root = tmp_path / "repo"
    root.mkdir()
    target = root / "main.py"
    target.write_text("v1 = 1\n", encoding="utf-8")
    attached = client.put(
        f"/api/projects/{project_id}/source-root",
        json={"absolute_path": str(root), "exclusions": []},
        headers=ORIGIN,
    )
    assert attached.status_code == 200, attached.text
    preview = client.post(
        f"/api/projects/{project_id}/code-context/preview",
        json={"relative_paths": ["main.py"]},
        headers=ORIGIN,
    )
    assert preview.status_code == 201, preview.text
    body = preview.json()
    assert body["files"][0]["content"] == "v1 = 1\n"
    assert body["reserves_budget"] is False
    assert body["provider_calls"] == 0
    target.write_text("v2 = 2\n", encoding="utf-8")
    frozen = client.post(
        f"/api/projects/{project_id}/code-snapshots",
        json={"preview_id": body["preview_id"]},
        headers=ORIGIN,
    )
    assert frozen.status_code == 201, frozen.text
    snap = frozen.json()
    assert snap["files"][0]["content"] == "v1 = 1\n"
    assert snap["fingerprint"] == body["fingerprint"]


def test_symlink_and_env_excluded(client: TestClient, tmp_path: Path) -> None:
    project_id = _project(client)
    root = tmp_path / "repo"
    root.mkdir()
    (root / "ok.py").write_text("print(1)\n", encoding="utf-8")
    (root / ".env").write_text("SECRET=1\n", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("leak\n", encoding="utf-8")
    (root / "link.py").symlink_to(outside)
    client.put(
        f"/api/projects/{project_id}/source-root",
        json={"absolute_path": str(root), "exclusions": []},
        headers=ORIGIN,
    )
    tree = client.get(f"/api/projects/{project_id}/source-tree", headers=ORIGIN)
    assert tree.status_code == 200
    entries = {item["relative_path"]: item for item in tree.json()["entries"]}
    assert entries[".env"]["excluded"] is True
    assert entries["link.py"]["kind"] == "symlink"
    bad = client.post(
        f"/api/projects/{project_id}/code-context/preview",
        json={"relative_paths": ["link.py"]},
        headers=ORIGIN,
    )
    assert bad.status_code == 422
    env_preview = client.post(
        f"/api/projects/{project_id}/code-context/preview",
        json={"relative_paths": [".env"]},
        headers=ORIGIN,
    )
    assert env_preview.status_code == 422


def test_project_isolation_on_snapshot_get(client: TestClient, tmp_path: Path) -> None:
    a = _project(client)
    b = client.post(
        "/api/projects",
        json={"name": "Other", "description": "Isolation"},
        headers=ORIGIN,
    ).json()["id"]
    root = tmp_path / "repo"
    root.mkdir()
    (root / "a.py").write_text("a\n", encoding="utf-8")
    client.put(
        f"/api/projects/{a}/source-root",
        json={"absolute_path": str(root), "exclusions": []},
        headers=ORIGIN,
    )
    preview = client.post(
        f"/api/projects/{a}/code-context/preview",
        json={"relative_paths": ["a.py"]},
        headers=ORIGIN,
    ).json()
    snap = client.post(
        f"/api/projects/{a}/code-snapshots",
        json={"preview_id": preview["preview_id"]},
        headers=ORIGIN,
    ).json()
    stolen = client.get(
        f"/api/projects/{b}/code-snapshots/{snap['snapshot_id']}",
        headers=ORIGIN,
    )
    assert stolen.status_code == 404


def test_real_review_without_code_sources_notice(client: TestClient) -> None:
    project_id = _project(client)
    created = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "Revue sans code",
            "idempotency_key": "no-code-1",
            "execution_mode": "real",
        },
        headers=ORIGIN,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["code_sources"]["has_code_sources"] is False
    assert "Aucune source fichier" in body["code_sources"]["notice"]
