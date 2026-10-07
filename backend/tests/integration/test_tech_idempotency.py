from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _project(client: TestClient) -> str:
    response = client.post(
        "/api/projects",
        json={"name": "Idem Proj", "description": "Tests d'idempotence TECH"},
        headers=ORIGIN,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _awaiting_security(client: TestClient) -> str:
    project_id = _project(client)
    created = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "sécurité auth secrets exposition",
            "idempotency_key": "create-await",
        },
        headers=ORIGIN,
    )
    review_id = created.json()["id"]
    client.post(
        f"/api/tech/reviews/{review_id}/scenario",
        json={"scenario_id": "security_critical"},
        headers=ORIGIN,
    )
    client.post(
        f"/api/tech/reviews/{review_id}/run",
        json={"idempotency_key": "run-await"},
        headers=ORIGIN,
    )
    return review_id


def _awaiting_local(client: TestClient, key_suffix: str) -> str:
    project_id = _project(client)
    created = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "persistance sqlite hexagonal",
            "idempotency_key": f"create-local-{key_suffix}",
        },
        headers=ORIGIN,
    )
    review_id = created.json()["id"]
    client.post(
        f"/api/tech/reviews/{review_id}/scenario",
        json={"scenario_id": "local_persistence"},
        headers=ORIGIN,
    )
    client.post(
        f"/api/tech/reviews/{review_id}/run",
        json={"idempotency_key": f"run-local-{key_suffix}"},
        headers=ORIGIN,
    )
    return review_id


def test_create_idempotent_and_payload_conflict(client: TestClient) -> None:
    project_id = _project(client)
    first = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "persistance sqlite",
            "idempotency_key": "same-key",
        },
        headers=ORIGIN,
    )
    second = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "persistance sqlite",
            "idempotency_key": "same-key",
        },
        headers=ORIGIN,
    )
    assert first.json()["id"] == second.json()["id"]
    conflict = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "autre demande",
            "idempotency_key": "same-key",
        },
        headers=ORIGIN,
    )
    assert conflict.status_code == 422
    assert conflict.json()["code"] == "idempotency_conflict"


def test_run_already_done_no_duplicate(client: TestClient) -> None:
    review_id = _awaiting_security(client)
    again = client.post(
        f"/api/tech/reviews/{review_id}/run",
        json={"idempotency_key": "brand-new-run-key"},
        headers=ORIGIN,
    )
    assert again.status_code == 200
    assert again.json()["status"] == "awaiting_decision"
    assert again.json()["proposals_version"] == 1


def test_decision_replay_and_conflict(client: TestClient) -> None:
    review_id = _awaiting_security(client)
    payload = {
        "proposal_id": "p-safe",
        "proposal_version": 1,
        "rationale": "Choix sûr et documenté.",
        "idempotency_key": "dec-replay",
    }
    first = client.post(
        f"/api/tech/reviews/{review_id}/decision",
        json=payload,
        headers=ORIGIN,
    )
    second = client.post(
        f"/api/tech/reviews/{review_id}/decision",
        json=payload,
        headers=ORIGIN,
    )
    assert first.json()["adr"]["id"] == second.json()["adr"]["id"]
    different = client.post(
        f"/api/tech/reviews/{review_id}/decision",
        json={
            "proposal_id": "p-danger",
            "proposal_version": 1,
            "rationale": "Autre choix après décision.",
            "idempotency_key": "dec-other",
        },
        headers=ORIGIN,
    )
    assert different.status_code == 422
    assert different.json()["code"] == "conflict"


def test_stale_version_rejected(client: TestClient) -> None:
    review_id = _awaiting_security(client)
    stale = client.post(
        f"/api/tech/reviews/{review_id}/decision",
        json={
            "proposal_id": "p-safe",
            "proposal_version": 9,
            "rationale": "Version obsolète volontaire.",
            "idempotency_key": "dec-stale",
        },
        headers=ORIGIN,
    )
    assert stale.status_code == 422
    assert stale.json()["code"] == "stale_proposal_version"


def test_unknown_fields_rejected(client: TestClient) -> None:
    project_id = _project(client)
    response = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "persistance",
            "idempotency_key": "extra-fields",
            "forced_agent_id": "architecte",
            "capability_ids": ["tech.analyze.architecture"],
        },
        headers=ORIGIN,
    )
    assert response.status_code == 422


def test_run_without_scenario_no_partial(client: TestClient) -> None:
    project_id = _project(client)
    created = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "persistance sqlite",
            "idempotency_key": "no-scenario",
        },
        headers=ORIGIN,
    )
    review_id = created.json()["id"]
    failed = client.post(
        f"/api/tech/reviews/{review_id}/run",
        json={"idempotency_key": "run-no-scenario"},
        headers=ORIGIN,
    )
    assert failed.status_code == 422
    fetched = client.get(f"/api/tech/reviews/{review_id}")
    assert fetched.json()["status"] == "selecting_scenario"
    assert fetched.json()["analyses"] == []
    assert fetched.json()["proposals"] == []


def test_concurrent_decisions_single_adr(client: TestClient) -> None:
    review_id = _awaiting_local(client, "conc")

    def choose(proposal_id: str, key: str):
        return client.post(
            f"/api/tech/reviews/{review_id}/decision",
            json={
                "proposal_id": proposal_id,
                "proposal_version": 1,
                "rationale": f"Choix concurrent pour {proposal_id}",
                "idempotency_key": key,
            },
            headers=ORIGIN,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(choose, "p-a", "conc-a"),
            pool.submit(choose, "p-b", "conc-b"),
        ]
        results = [item.result() for item in futures]
    successes = [item for item in results if item.status_code == 200]
    assert len(successes) == 1
    final = client.get(f"/api/tech/reviews/{review_id}")
    assert final.json()["status"] == "decided"
    assert final.json()["adr"] is not None
