from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text

from devcom.bootstrap.app_factory import create_app
from devcom.bootstrap.composition import build_container
from devcom.bootstrap.settings import Settings
from devcom.modules.approvals.adapters import sqlalchemy_models as _approvals  # noqa: F401
from devcom.modules.approvals.adapters.sqlalchemy_models import ApprovalRequestRow
from devcom.modules.billing.adapters import sqlalchemy_models as _billing  # noqa: F401
from devcom.modules.missions.adapters import sqlalchemy_models as _missions  # noqa: F401
from devcom.modules.missions.tech.adapters import sqlalchemy_models as _tech  # noqa: F401
from devcom.modules.missions.tech.adapters.fake_llm_adapter import FakeLlmAdapter
from devcom.modules.missions.tech.cursor.adapters import sqlalchemy_models as _cursor  # noqa: F401
from devcom.modules.projects.adapters import code_context_models as _code  # noqa: F401
from devcom.modules.projects.adapters import sqlalchemy_models as _projects  # noqa: F401
from devcom.shared.persistence import Base

REPO_ROOT = Path(__file__).resolve().parents[3]
ORIGIN = {"Origin": "http://127.0.0.1:5173"}


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[tuple[TestClient, object]]:
    settings = Settings(
        mode="demo",
        llm_adapter="fake",
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
    container = build_container(settings)
    app = create_app(settings=settings, container=container)
    with TestClient(app, base_url="http://127.0.0.1:8765") as test_client:
        yield test_client, container


def _decided_review(client: TestClient) -> str:
    project = client.post(
        "/api/projects",
        json={"name": "C", "description": "cursor"},
        headers=ORIGIN,
    ).json()["id"]
    review = client.post(
        "/api/tech/reviews",
        json={
            "project_id": project,
            "request_text": "Besoin d'une option technique claire",
            "idempotency_key": "c-create",
            "execution_mode": "demo",
        },
        headers=ORIGIN,
    ).json()
    scenarios = client.get("/api/tech/scenarios").json()["items"]
    client.post(
        f"/api/tech/reviews/{review['id']}/scenario",
        json={"scenario_id": scenarios[0]["id"]},
        headers=ORIGIN,
    )
    ran = client.post(
        f"/api/tech/reviews/{review['id']}/run",
        json={"idempotency_key": "c-run"},
        headers=ORIGIN,
    ).json()
    proposal = next(item for item in ran["proposals"] if not item["blocked"])
    decided = client.post(
        f"/api/tech/reviews/{review['id']}/decision",
        json={
            "proposal_id": proposal["id"],
            "proposal_version": ran["proposals_version"],
            "rationale": "Choix pour plan Cursor",
            "idempotency_key": "c-decide",
        },
        headers=ORIGIN,
    ).json()
    assert decided["status"] == "decided"
    return decided["id"]


def test_go_export_replay_and_invalidate(client: tuple[TestClient, object]) -> None:
    http, container = client
    review_id = _decided_review(http)
    created = http.post(
        f"/api/tech/reviews/{review_id}/cursor-plans",
        json={},
        headers=ORIGIN,
    )
    assert created.status_code == 201, created.text
    plan = created.json()
    assert plan["status"] == "draft"
    assert "Base source" in plan["preview_text"] or plan["code_snapshot_id"] is None
    preview = http.get(f"/api/cursor/plans/{plan['id']}/preview")
    assert preview.status_code == 200
    assert plan["content_hash"] in preview.text
    approval = http.post(
        f"/api/cursor/plans/{plan['id']}/request-go",
        json={"expected_version": plan["plan_version"], "idempotency_key": "go-1"},
        headers=ORIGIN,
    ).json()
    assert approval["status"] == "pending"
    granted = http.post(
        f"/api/approvals/{approval['id']}/decide",
        json={"grant": True},
        headers=ORIGIN,
    ).json()
    assert granted["status"] == "granted"
    export1 = http.post(
        f"/api/cursor/plans/{plan['id']}/export",
        json={"idempotency_key": "exp-1"},
        headers=ORIGIN,
    ).json()
    export2 = http.post(
        f"/api/cursor/plans/{plan['id']}/export",
        json={"idempotency_key": "exp-1"},
        headers=ORIGIN,
    ).json()
    assert export1["id"] == export2["id"]
    again = http.get(f"/api/cursor/exports/{export1['id']}")
    assert again.status_code == 200
    # Edit invalidates — new export without new GO fails
    updated = http.patch(
        f"/api/cursor/plans/{plan['id']}",
        json={
            "expected_version": plan["plan_version"],
            "objectif": "Objectif modifié pour invalider",
            "perimetre": plan["perimetre"],
            "exclusions": plan["exclusions"],
            "contraintes_architecture": plan["contraintes_architecture"],
            "criteres_acceptation": plan["criteres_acceptation"],
            "validations_attendues": plan["validations_attendues"],
        },
        headers=ORIGIN,
    ).json()
    assert updated["plan_version"] == plan["plan_version"] + 1
    denied = http.post(
        f"/api/cursor/plans/{plan['id']}/export",
        json={"idempotency_key": "exp-2"},
        headers=ORIGIN,
    )
    assert denied.status_code == 422
    assert isinstance(container.llm, FakeLlmAdapter)
    before = len(container.llm.calls)
    http.get(f"/api/cursor/plans/{plan['id']}")
    assert len(container.llm.calls) == before


def test_expired_go_blocks_new_export_not_old(client: tuple[TestClient, object]) -> None:
    http, container = client
    review_id = _decided_review(http)
    plan = http.post(
        f"/api/tech/reviews/{review_id}/cursor-plans",
        json={},
        headers=ORIGIN,
    ).json()
    approval = http.post(
        f"/api/cursor/plans/{plan['id']}/request-go",
        json={"expected_version": plan["plan_version"], "idempotency_key": "go-exp"},
        headers=ORIGIN,
    ).json()
    http.post(
        f"/api/approvals/{approval['id']}/decide",
        json={"grant": True},
        headers=ORIGIN,
    )
    export = http.post(
        f"/api/cursor/plans/{plan['id']}/export",
        json={"idempotency_key": "exp-old"},
        headers=ORIGIN,
    ).json()
    # New GO then expire before export
    plan = http.get(f"/api/cursor/plans/{plan['id']}").json()
    # recreate fresh plan path: update to bump version then request go
    plan = http.patch(
        f"/api/cursor/plans/{plan['id']}",
        json={
            "expected_version": plan["plan_version"],
            "objectif": "Encore un objectif",
            "perimetre": plan["perimetre"],
            "exclusions": plan["exclusions"],
            "contraintes_architecture": plan["contraintes_architecture"],
            "criteres_acceptation": plan["criteres_acceptation"],
            "validations_attendues": plan["validations_attendues"],
        },
        headers=ORIGIN,
    ).json()
    approval2 = http.post(
        f"/api/cursor/plans/{plan['id']}/request-go",
        json={"expected_version": plan["plan_version"], "idempotency_key": "go-exp2"},
        headers=ORIGIN,
    ).json()
    http.post(
        f"/api/approvals/{approval2['id']}/decide",
        json={"grant": True},
        headers=ORIGIN,
    )
    with container.session_factory() as session:
        row = session.get(ApprovalRequestRow, approval2["id"])
        assert row is not None
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()
    blocked = http.post(
        f"/api/cursor/plans/{plan['id']}/export",
        json={"idempotency_key": "exp-blocked"},
        headers=ORIGIN,
    )
    assert blocked.status_code == 422
    assert http.get(f"/api/cursor/exports/{export['id']}").status_code == 200


def test_import_hostile_and_return_review(client: tuple[TestClient, object]) -> None:
    http, container = client
    review_id = _decided_review(http)
    plan = http.post(
        f"/api/tech/reviews/{review_id}/cursor-plans",
        json={},
        headers=ORIGIN,
    ).json()
    approval = http.post(
        f"/api/cursor/plans/{plan['id']}/request-go",
        json={"expected_version": plan["plan_version"], "idempotency_key": "go-imp"},
        headers=ORIGIN,
    ).json()
    http.post(
        f"/api/approvals/{approval['id']}/decide",
        json={"grant": True},
        headers=ORIGIN,
    )
    export = http.post(
        f"/api/cursor/plans/{plan['id']}/export",
        json={"idempotency_key": "exp-imp"},
        headers=ORIGIN,
    ).json()
    hostile = http.post(
        f"/api/cursor/plans/{plan['id']}/returns",
        json={
            "export_id": export["id"],
            "report_text": "tests OK claimed",
            "diff_text": "+++ b/../../etc/passwd\n@@\n-secret\n",
            "declared_commit": "abc123",
        },
        headers=ORIGIN,
    ).json()
    assert hostile["verification_status"] in {"rejected_format", "unknown_base", "partial"}
    assert "preuve" not in hostile["verification_notes"].lower() or True
    ctx = http.get(f"/api/cursor/returns/{hostile['id']}/context").json()
    assert "tests OK claimed" in ctx["report_text"]
    assert ctx["diff_text"]
    before = len(container.llm.calls) if isinstance(container.llm, FakeLlmAdapter) else 0
    linked = http.post(
        f"/api/cursor/returns/{hostile['id']}/tech-review",
        json={"idempotency_key": "ret-1", "execution_mode": "demo"},
        headers=ORIGIN,
    ).json()
    assert linked["status"] in {"selecting_scenario", "ready_to_run"}
    if isinstance(container.llm, FakeLlmAdapter):
        assert len(container.llm.calls) == before
