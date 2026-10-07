from __future__ import annotations

from fastapi.testclient import TestClient

from devcom.bootstrap.app_factory import create_app
from devcom.bootstrap.composition import build_container


def _create_project(client: TestClient) -> str:
    response = client.post(
        "/api/projects",
        json={"name": "Mission Proj", "description": "Pour lot 1"},
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_mission(client: TestClient, project_id: str, text: str):
    return client.post(
        "/api/missions",
        json={"project_id": project_id, "request_text": text},
        headers={"Origin": "http://127.0.0.1:5173"},
    )


def test_mail_mission_routes_to_secretaire(client: TestClient) -> None:
    project_id = _create_project(client)
    created = _create_mission(client, project_id, "Classer ces mails")
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "routed"
    assert body["routing"]["mode"] == "demo_deterministic"
    assert [task["agent_id"] for task in body["tasks"]] == ["secretaire"]


def test_sqlite_mission_two_tasks(client: TestClient) -> None:
    project_id = _create_project(client)
    created = _create_mission(client, project_id, "Concevoir la persistance SQLite")
    assert created.status_code == 201
    agents = {task["agent_id"] for task in created.json()["tasks"]}
    assert agents == {"sql_data", "architecte"}


def test_mixed_mission_splits_tasks(client: TestClient) -> None:
    project_id = _create_project(client)
    mixed = _create_mission(
        client,
        project_id,
        "Qualifier un prospect commercial et évaluer l'API technique",
    )
    assert mixed.status_code == 201
    assert len(mixed.json()["tasks"]) == 2


def test_external_blocks_without_execution(client: TestClient) -> None:
    project_id = _create_project(client)
    external = _create_mission(client, project_id, "Envoyer ce mail au client")
    assert external.status_code == 201
    body = external.json()
    assert body["status"] == "blocked_authorization"
    assert body["tasks"] == []
    assert "préciser" in body["authorization_block"]["message"]


def test_clarification_then_stale_token(client: TestClient) -> None:
    project_id = _create_project(client)
    unknown = _create_mission(
        client,
        project_id,
        "Optimiser la stratégie globale de l'univers",
    )
    body = unknown.json()
    token = body["clarification_token"]
    question_id = body["clarification_questions"][0]["id"]
    answered = client.post(
        f"/api/missions/{body['id']}/clarifications",
        json={"clarification_token": token, "answers": {question_id: "mail"}},
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert answered.status_code == 200
    assert answered.json()["status"] == "routed"
    stale = client.post(
        f"/api/missions/{body['id']}/clarifications",
        json={"clarification_token": token, "answers": {question_id: "sqlite"}},
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert stale.status_code == 422
    assert stale.json()["code"] == "stale_clarification"


def test_mission_survives_restart(client: TestClient, migrated_settings) -> None:
    project_id = _create_project(client)
    created = _create_mission(client, project_id, "Classer ces mails")
    mission_id = created.json()["id"]
    second = build_container(migrated_settings)
    app2 = create_app(settings=migrated_settings, container=second)
    with TestClient(app2, base_url="http://127.0.0.1:8765") as client2:
        fetched = client2.get(f"/api/missions/{mission_id}")
        assert fetched.status_code == 200
        assert fetched.json()["status"] == "routed"


def test_foreign_key_rejects_unknown_project(client: TestClient) -> None:
    response = _create_mission(
        client,
        "00000000-0000-0000-0000-000000000099",
        "Classer ces mails",
    )
    assert response.status_code == 422
    assert response.json()["code"] == "project_not_found"
