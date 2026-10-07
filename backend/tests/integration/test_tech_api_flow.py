from __future__ import annotations

from fastapi.testclient import TestClient

from devcom.bootstrap.app_factory import create_app
from devcom.bootstrap.composition import build_container

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _project(client: TestClient) -> str:
    response = client.post(
        "/api/projects",
        json={"name": "Tech Proj", "description": "Contexte revue TECH"},
        headers=ORIGIN,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create(client: TestClient, project_id: str, text: str, key: str):
    return client.post(
        "/api/tech/reviews",
        json={"project_id": project_id, "request_text": text, "idempotency_key": key},
        headers=ORIGIN,
    )


def _select_and_run(client: TestClient, review_id: str, scenario: str, run_key: str):
    selected = client.post(
        f"/api/tech/reviews/{review_id}/scenario",
        json={"scenario_id": scenario},
        headers=ORIGIN,
    )
    assert selected.status_code == 200
    ran = client.post(
        f"/api/tech/reviews/{review_id}/run",
        json={"idempotency_key": run_key},
        headers=ORIGIN,
    )
    assert ran.status_code == 200
    return selected.json(), ran.json()


def test_snapshot_frozen_after_project_rename(client: TestClient) -> None:
    project_id = _project(client)
    created = _create(client, project_id, "Concevoir la persistance SQLite", "c-snap")
    review_id = created.json()["id"]
    selected = client.post(
        f"/api/tech/reviews/{review_id}/scenario",
        json={"scenario_id": "local_persistence"},
        headers=ORIGIN,
    )
    snapshot_name = selected.json()["snapshot"]["project_name"]
    renamed = client.patch(
        f"/api/projects/{project_id}",
        json={"name": "Nom modifié après snapshot", "description": "Contexte revue TECH"},
        headers=ORIGIN,
    )
    assert renamed.status_code == 200
    ran = client.post(
        f"/api/tech/reviews/{review_id}/run",
        json={"idempotency_key": "run-snap"},
        headers=ORIGIN,
    )
    assert ran.json()["snapshot"]["project_name"] == snapshot_name


def test_full_local_persistence_flow(client: TestClient) -> None:
    project_id = _project(client)
    created = _create(client, project_id, "Concevoir la persistance SQLite", "c-local-1")
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "selecting_scenario"
    assert body["suggested_scenario_id"] == "local_persistence"
    _selected, ran = _select_and_run(
        client, body["id"], "local_persistence", "run-local-1"
    )
    assert ran["status"] == "awaiting_decision"
    assert len(ran["analyses"]) == 6
    assert ran["synthesis"]["disagreements"]
    assert all(not item["blocked"] for item in ran["proposals"])
    decided = client.post(
        f"/api/tech/reviews/{body['id']}/decision",
        json={
            "proposal_id": "p-a",
            "proposal_version": 1,
            "rationale": "Je retiens les frontières modulaires.",
            "idempotency_key": "dec-local-1",
        },
        headers=ORIGIN,
    )
    assert decided.status_code == 200
    final = decided.json()
    assert final["status"] == "decided"
    assert final["decision"]["author"] == "local-demo-user"
    assert "démonstration" in final["adr"]["demo_warning"].casefold()
    assert len(final["proposals"]) == 2


def test_security_blocks_and_allows_safe(client: TestClient) -> None:
    project_id = _project(client)
    created = _create(client, project_id, "Revue sécurité auth secrets", "c-sec-1")
    review_id = created.json()["id"]
    _selected, ran = _select_and_run(
        client, review_id, "security_critical", "run-sec-1"
    )
    blocked = next(item for item in ran["proposals"] if item["id"] == "p-danger")
    safe = next(item for item in ran["proposals"] if item["id"] == "p-safe")
    assert blocked["blocked"] is True
    assert blocked["lift_conditions"]
    assert safe["blocked"] is False
    refused = client.post(
        f"/api/tech/reviews/{review_id}/decision",
        json={
            "proposal_id": "p-danger",
            "proposal_version": 1,
            "rationale": "Je veux forcer la proposition dangereuse.",
            "idempotency_key": "dec-sec-bad",
        },
        headers=ORIGIN,
    )
    assert refused.status_code == 422
    assert refused.json()["code"] == "proposal_blocked"
    ok = client.post(
        f"/api/tech/reviews/{review_id}/decision",
        json={
            "proposal_id": "p-safe",
            "proposal_version": 1,
            "rationale": "Redaction et références opaques.",
            "idempotency_key": "dec-sec-ok",
        },
        headers=ORIGIN,
    )
    assert ok.status_code == 200
    assert ok.json()["decision"]["proposal_id"] == "p-safe"


def test_unmatched_request_disclaimer(client: TestClient) -> None:
    project_id = _project(client)
    created = _create(
        client,
        project_id,
        "Optimiser la stratégie galactique sans mot-clé",
        "c-unmatched",
    )
    assert created.json()["unmatched_request"] is True
    review_id = created.json()["id"]
    selected = client.post(
        f"/api/tech/reviews/{review_id}/scenario",
        json={"scenario_id": "local_persistence"},
        headers=ORIGIN,
    )
    note = selected.json()["scenario_label_note"]
    assert note is not None
    assert "n'a pas été analysée librement" in note


def test_mission_does_not_create_tech_review(client: TestClient) -> None:
    project_id = _project(client)
    mission = client.post(
        "/api/missions",
        json={
            "project_id": project_id,
            "request_text": "Concevoir la persistance SQLite",
        },
        headers=ORIGIN,
    )
    assert mission.status_code == 201
    reviews = client.get("/api/tech/reviews")
    assert reviews.json()["items"] == []


def test_restart_persists_review(client: TestClient, migrated_settings) -> None:
    project_id = _project(client)
    created = _create(client, project_id, "persistance sqlite hexagonale", "c-restart")
    review_id = created.json()["id"]
    _select_and_run(client, review_id, "local_persistence", "run-restart")
    second = build_container(migrated_settings)
    app2 = create_app(settings=migrated_settings, container=second)
    with TestClient(app2, base_url="http://127.0.0.1:8765") as client2:
        fetched = client2.get(f"/api/tech/reviews/{review_id}")
        assert fetched.status_code == 200
        assert fetched.json()["status"] == "awaiting_decision"
        assert len(fetched.json()["analyses"]) == 6
