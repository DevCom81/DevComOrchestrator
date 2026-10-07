from __future__ import annotations

from fastapi.testclient import TestClient

from devcom.bootstrap.app_factory import create_app
from devcom.bootstrap.composition import build_container
from devcom.bootstrap.settings import Settings


def test_project_survives_new_container(migrated_settings: Settings) -> None:
    first = build_container(migrated_settings)
    app1 = create_app(settings=migrated_settings, container=first)
    with TestClient(app1, base_url="http://127.0.0.1:8765") as client:
        created = client.post(
            "/api/projects",
            json={"name": "Persist", "description": "Avant redémarrage"},
            headers={"Origin": "http://127.0.0.1:5173"},
        )
        assert created.status_code == 201
        project_id = created.json()["id"]
        patched = client.patch(
            f"/api/projects/{project_id}",
            json={"description": "Après modification"},
            headers={"Origin": "http://127.0.0.1:5173"},
        )
        assert patched.status_code == 200

    second = build_container(migrated_settings)
    app2 = create_app(settings=migrated_settings, container=second)
    with TestClient(app2, base_url="http://127.0.0.1:8765") as client:
        fetched = client.get(f"/api/projects/{project_id}")
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "Persist"
        assert fetched.json()["description"] == "Après modification"
