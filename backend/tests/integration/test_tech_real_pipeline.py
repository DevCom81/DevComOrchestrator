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
from devcom.modules.missions.tech.adapters.fake_llm_adapter import FakeLlmAdapter
from devcom.modules.missions.tech.domain.status import TechReviewStatus
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
def real_client(real_settings: Settings) -> Iterator[TestClient]:
    container = build_container(real_settings)
    app = create_app(settings=real_settings, container=container)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        yield client


def _project(client: TestClient) -> str:
    response = client.post(
        "/api/projects",
        json={"name": "Real Proj", "description": "Contexte revue réelle"},
        headers=ORIGIN,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _wait_terminal(client: TestClient, review_id: str) -> dict:
    final: dict | None = None
    for _ in range(80):
        polled = client.get(f"/api/tech/reviews/{review_id}")
        assert polled.status_code == 200
        final = polled.json()
        if final["status"] == "running":
            continue
        # Ambiguous cost may keep reservation held intentionally.
        if final["status"] == "blocked_uncertain":
            return final
        # Avoid racing the finally settle when status flips first.
        if final.get("reservation_status") == "held":
            continue
        return final
    assert final is not None
    return final


def test_real_pipeline_happy_path_with_fake_llm(real_client: TestClient) -> None:
    project_id = _project(real_client)
    created = real_client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "Revue réelle courte sous un euro",
            "idempotency_key": "real-create-1",
            "execution_mode": "real",
        },
        headers=ORIGIN,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["execution_mode"] == "real"
    assert body["status"] == "ready_to_run"
    assert body["envelope_eur_micros"] <= 1_000_000
    assert body["frozen_plan"]["max_calls"] == 19

    started = real_client.post(
        f"/api/tech/reviews/{body['id']}/run",
        json={"idempotency_key": "real-run-1"},
        headers=ORIGIN,
    )
    assert started.status_code == 200, started.text
    final = _wait_terminal(real_client, body["id"])
    assert final["status"] == "awaiting_decision"
    assert len(final["analyses"]) == 6
    assert final["synthesis"] is not None
    assert any(step["status"] == "skipped" for step in final["steps"] if step["phase"] == "reply")
    assert all(item["cost_status"] == "confirmed" for item in final["usage"])
    assert final["reservation_status"] == "settled"


def test_get_never_triggers_llm_calls(real_settings: Settings) -> None:
    container = build_container(real_settings)
    app = create_app(settings=real_settings, container=container)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        project_id = _project(client)
        created = client.post(
            "/api/tech/reviews",
            json={
                "project_id": project_id,
                "request_text": "poll only",
                "idempotency_key": "poll-1",
                "execution_mode": "real",
            },
            headers=ORIGIN,
        )
        review_id = created.json()["id"]
        llm = container.llm
        assert isinstance(llm, FakeLlmAdapter)
        before = list(llm.calls)
        client.get(f"/api/tech/reviews/{review_id}")
        client.get(f"/api/tech/reviews/{review_id}")
        assert llm.calls == before


def test_second_real_run_blocked_while_first_active(real_client: TestClient) -> None:
    project_id = _project(real_client)
    first = real_client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "first",
            "idempotency_key": "lock-1",
            "execution_mode": "real",
        },
        headers=ORIGIN,
    ).json()
    second = real_client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "second",
            "idempotency_key": "lock-2",
            "execution_mode": "real",
        },
        headers=ORIGIN,
    ).json()
    r1 = real_client.post(
        f"/api/tech/reviews/{first['id']}/run",
        json={"idempotency_key": "run-lock-1"},
        headers=ORIGIN,
    )
    r2 = real_client.post(
        f"/api/tech/reviews/{second['id']}/run",
        json={"idempotency_key": "run-lock-2"},
        headers=ORIGIN,
    )
    assert r1.status_code == 200
    assert r2.status_code == 422
    assert r2.json()["code"] == "pipeline_lock"
    _wait_terminal(real_client, first["id"])


def test_in_flight_marked_uncertain(real_settings: Settings) -> None:
    container = build_container(real_settings)
    app = create_app(settings=real_settings, container=container)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        project_id = _project(client)
        created = client.post(
            "/api/tech/reviews",
            json={
                "project_id": project_id,
                "request_text": "crash frontier",
                "idempotency_key": "crash-1",
                "execution_mode": "real",
            },
            headers=ORIGIN,
        )
        review_id = created.json()["id"]
        container.step_store.replace_plan(
            review_id,
            [
                {
                    "step_key": "analyze:architecte",
                    "phase": "analyze",
                    "agent_id": "architecte",
                    "optional": False,
                }
            ],
        )
        assert container.step_store.mark(review_id, "analyze:architecte", status="in_flight")
        from devcom.modules.missions.tech.adapters.sqlalchemy_models import TechReviewRow

        with container.session_factory() as session:
            row = session.get(TechReviewRow, review_id)
            assert row is not None
            row.status = TechReviewStatus.RUNNING.value
            session.commit()
        marked = container.step_store.mark_in_flight_uncertain(review_id)
        assert marked == 1
        assert container.step_store.list_steps(review_id)[0]["status"] == "uncertain"


def test_demo_mode_refuses_real_create(client: TestClient) -> None:
    project = client.post(
        "/api/projects",
        json={"name": "D", "description": "x"},
        headers=ORIGIN,
    ).json()["id"]
    response = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project,
            "request_text": "should fail",
            "idempotency_key": "demo-refuse",
            "execution_mode": "real",
        },
        headers=ORIGIN,
    )
    assert response.status_code == 422
    assert response.json()["code"] == "real_mode_unavailable"


def test_invalid_result_still_records_usage(real_settings: Settings) -> None:
    container = build_container(real_settings)
    assert isinstance(container.llm, FakeLlmAdapter)
    container.llm._scripted["analyze:architecte"] = {
        "ok": False,
        "parsed": None,
        "input_tokens": 10,
        "output_tokens": 5,
        "error_code": "invalid_json",
        "error_message": "bad json",
    }
    app = create_app(settings=real_settings, container=container)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        project_id = _project(client)
        created = client.post(
            "/api/tech/reviews",
            json={
                "project_id": project_id,
                "request_text": "invalid first",
                "idempotency_key": "inv-1",
                "execution_mode": "real",
            },
            headers=ORIGIN,
        )
        review_id = created.json()["id"]
        client.post(
            f"/api/tech/reviews/{review_id}/run",
            json={"idempotency_key": "inv-run"},
            headers=ORIGIN,
        )
        final = _wait_terminal(client, review_id)
        assert final["status"] == "failed_partial"
        assert final["usage"]
        assert final["usage"][0]["cost_status"] == "confirmed"
        assert final["usage"][0]["result_status"] == "invalid"
