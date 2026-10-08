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
from devcom.modules.missions.tech.adapters.sqlalchemy_events import SqlAlchemyEventStore
from devcom.modules.missions.tech.adapters.sqlalchemy_models import TechReviewRow
from devcom.modules.missions.tech.application.reconcile_real import (
    reconcile_interrupted_real_pipeline,
)
from devcom.modules.missions.tech.domain.status import TechReviewStatus
from devcom.modules.projects.adapters import sqlalchemy_models as _projects  # noqa: F401
from devcom.shared.persistence import Base
from devcom.shared.time import SystemClock

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
def real_client(real_settings: Settings) -> Iterator[tuple[TestClient, object]]:
    container = build_container(real_settings)
    app = create_app(settings=real_settings, container=container)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        yield client, container


def _project(client: TestClient) -> str:
    response = client.post(
        "/api/projects",
        json={"name": "Durability", "description": "LOT5"},
        headers=ORIGIN,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_real(client: TestClient, project_id: str, key: str) -> str:
    created = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project_id,
            "request_text": "durability review",
            "idempotency_key": key,
            "execution_mode": "real",
        },
        headers=ORIGIN,
    )
    assert created.status_code == 201
    return created.json()["id"]


def test_reconcile_interrupted_before_calls(real_client: tuple[TestClient, object]) -> None:
    client, container = real_client
    review_id = _create_real(client, _project(client), "dur-int-1")
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
    container.budget_ledger.reserve_review_envelope(
        review_id=review_id,
        envelope_usd_micros=1000,
        envelope_eur_micros=1000,
        fx_rate="0.9",
        fx_rate_date="2026-01-01",
        fx_margin_ratio="0.05",
        rates_verified_at="2026-01-01",
        now=SystemClock().now(),
    )
    with container.session_factory() as session:
        row = session.get(TechReviewRow, review_id)
        assert row is not None
        row.status = TechReviewStatus.RUNNING.value
        session.commit()
    events = SqlAlchemyEventStore(container.session_factory)
    first = reconcile_interrupted_real_pipeline(
        session_factory=container.session_factory,
        steps=container.step_store,
        ledger=container.budget_ledger,
        events=events,
        clock=SystemClock(),
    )
    second = reconcile_interrupted_real_pipeline(
        session_factory=container.session_factory,
        steps=container.step_store,
        ledger=container.budget_ledger,
        events=events,
        clock=SystemClock(),
    )
    assert first >= 1
    assert second == 0
    detail = client.get(f"/api/tech/reviews/{review_id}").json()
    assert detail["status"] == "interrupted"
    assert detail["reservation_status"] == "settled"
    journal = client.get(f"/api/tech/reviews/{review_id}/events").json()
    types = [item["event_type"] for item in journal["items"]]
    assert types.count("review.interrupted") == 1


def test_reconcile_blocked_uncertain_keeps_reservation(
    real_client: tuple[TestClient, object],
) -> None:
    client, container = real_client
    review_id = _create_real(client, _project(client), "dur-unc-1")
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
    container.budget_ledger.reserve_review_envelope(
        review_id=review_id,
        envelope_usd_micros=2000,
        envelope_eur_micros=2000,
        fx_rate="0.9",
        fx_rate_date="2026-01-01",
        fx_margin_ratio="0.05",
        rates_verified_at="2026-01-01",
        now=SystemClock().now(),
    )
    with container.session_factory() as session:
        row = session.get(TechReviewRow, review_id)
        assert row is not None
        row.status = TechReviewStatus.RUNNING.value
        session.commit()
    events = SqlAlchemyEventStore(container.session_factory)
    reconcile_interrupted_real_pipeline(
        session_factory=container.session_factory,
        steps=container.step_store,
        ledger=container.budget_ledger,
        events=events,
        clock=SystemClock(),
    )
    detail = client.get(f"/api/tech/reviews/{review_id}").json()
    assert detail["status"] == "blocked_uncertain"
    assert detail["reservation_status"] == "held"
    assert container.step_store.list_steps(review_id)[0]["status"] == "uncertain"
    ack = client.post(
        f"/api/tech/reviews/{review_id}/acknowledge-uncertainty",
        json={"reason": "vu en revue humaine", "idempotency_key": "ack-1"},
        headers=ORIGIN,
    )
    assert ack.status_code == 200
    body = ack.json()
    assert body["uncertainty_ack_at"] is not None
    assert body["reservation_status"] == "held"


def test_happy_path_emits_events(real_client: tuple[TestClient, object]) -> None:
    client, _container = real_client
    project_id = _project(client)
    review_id = _create_real(client, project_id, "dur-happy-1")
    started = client.post(
        f"/api/tech/reviews/{review_id}/run",
        json={"idempotency_key": "run-dur-1"},
        headers=ORIGIN,
    )
    assert started.status_code == 200
    final = None
    for _ in range(80):
        polled = client.get(f"/api/tech/reviews/{review_id}").json()
        if polled["status"] != "running" and polled.get("reservation_status") != "held":
            final = polled
            break
    assert final is not None
    assert final["status"] == "awaiting_decision"
    journal = client.get(f"/api/tech/reviews/{review_id}/events?after_seq=0").json()
    assert journal["latest_seq"] >= 1
    types = {item["event_type"] for item in journal["items"]}
    assert "review.started" in types
    assert "step.started" in types
    assert "budget.usage" in types
    listed = client.get(f"/api/tech/reviews?project_id={project_id}").json()
    assert any(item["id"] == review_id for item in listed["items"])


def test_get_and_events_do_not_call_llm(real_client: tuple[TestClient, object]) -> None:
    client, container = real_client
    review_id = _create_real(client, _project(client), "dur-nollm-1")
    client.post(
        f"/api/tech/reviews/{review_id}/run",
        json={"idempotency_key": "run-nollm-1"},
        headers=ORIGIN,
    )
    for _ in range(80):
        body = client.get(f"/api/tech/reviews/{review_id}").json()
        if body["status"] != "running" and body.get("reservation_status") != "held":
            break
    assert isinstance(container.llm, FakeLlmAdapter)
    before = len(container.llm.calls)
    assert client.get(f"/api/tech/reviews/{review_id}").status_code == 200
    assert client.get(f"/api/tech/reviews/{review_id}/events").status_code == 200
    assert len(container.llm.calls) == before
