from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_list_get_patch_project(client: TestClient) -> None:
    created = client.post(
        "/api/projects",
        json={"name": "Alpha", "description": "Premier projet"},
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert created.status_code == 201
    body = created.json()
    project_id = body["id"]
    assert body["name"] == "Alpha"

    listed = client.get("/api/projects")
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    fetched = client.get(f"/api/projects/{project_id}")
    assert fetched.status_code == 200
    assert fetched.json()["description"] == "Premier projet"

    updated = client.patch(
        f"/api/projects/{project_id}",
        json={"description": "Mis à jour"},
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Mis à jour"


def test_validation_and_not_found(client: TestClient) -> None:
    invalid = client.post(
        "/api/projects",
        json={"name": "   ", "description": "x"},
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert invalid.status_code == 422

    missing = client.get("/api/projects/00000000-0000-0000-0000-000000000099")
    assert missing.status_code == 404
    assert missing.json()["code"] == "project_not_found"


def test_mutation_rejects_bad_origin(client: TestClient) -> None:
    response = client.post(
        "/api/projects",
        json={"name": "Alpha", "description": "Premier projet"},
        headers={"Origin": "http://evil.example"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "invalid_origin"


def test_agents_catalogue(client: TestClient) -> None:
    response = client.get("/api/agents")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 11
    assert items[0]["id"] == "architecte"
    assert "operational" not in items[0]
    assert "state" not in items[0]


def test_runtime_demo(client: TestClient) -> None:
    response = client.get("/api/runtime")
    assert response.status_code == 200
    assert response.json()["mode"] == "demo"
