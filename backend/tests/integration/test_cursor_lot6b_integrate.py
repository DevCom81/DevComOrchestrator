from __future__ import annotations

import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text

from devcom.bootstrap.app_factory import create_app
from devcom.bootstrap.composition import build_container
from devcom.bootstrap.settings import Settings
from devcom.modules.approvals.adapters import sqlalchemy_models as _approvals  # noqa: F401
from devcom.modules.billing.adapters import sqlalchemy_models as _billing  # noqa: F401
from devcom.modules.missions.adapters import sqlalchemy_models as _missions  # noqa: F401
from devcom.modules.missions.tech.adapters import sqlalchemy_models as _tech  # noqa: F401
from devcom.modules.missions.tech.cursor.adapters import sqlalchemy_models as _cursor  # noqa: F401
from devcom.modules.projects.adapters import code_context_models as _code  # noqa: F401
from devcom.modules.projects.adapters import sqlalchemy_models as _projects  # noqa: F401
from devcom.shared.persistence import Base

REPO_ROOT = Path(__file__).resolve().parents[3]
ORIGIN = {"Origin": "http://127.0.0.1:5173"}


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[tuple[TestClient, Path]]:
    git_root = tmp_path / "src_repo"
    git_root.mkdir()
    (git_root / "hello.py").write_text(
        "def greet(name: str) -> str:\n    raise NotImplementedError\n"
    )
    subprocess.run(["git", "init", "-b", "main"], cwd=git_root, check=True)
    subprocess.run(["git", "add", "."], cwd=git_root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "base"],
        cwd=git_root,
        check=True,
    )
    settings = Settings(
        mode="demo",
        llm_adapter="fake",
        cursor_adapter="fake",
        host="127.0.0.1",
        port=8765,
        data_dir=tmp_path / "data",
        cors_origins="http://127.0.0.1:5173",
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
        yield test_client, git_root


def _decided_review(http: TestClient) -> str:
    project = http.post(
        "/api/projects",
        json={"name": "I", "description": "integrate"},
        headers=ORIGIN,
    ).json()["id"]
    review = http.post(
        "/api/tech/reviews",
        json={
            "project_id": project,
            "request_text": "Besoin d'une option",
            "idempotency_key": "i-create",
            "execution_mode": "demo",
        },
        headers=ORIGIN,
    ).json()
    scenarios = http.get("/api/tech/scenarios").json()["items"]
    http.post(
        f"/api/tech/reviews/{review['id']}/scenario",
        json={"scenario_id": scenarios[0]["id"]},
        headers=ORIGIN,
    )
    ran = http.post(
        f"/api/tech/reviews/{review['id']}/run",
        json={"idempotency_key": "i-run"},
        headers=ORIGIN,
    ).json()
    proposal = next(item for item in ran["proposals"] if not item["blocked"])
    decided = http.post(
        f"/api/tech/reviews/{review['id']}/decision",
        json={
            "proposal_id": proposal["id"],
            "proposal_version": ran["proposals_version"],
            "rationale": "go",
            "idempotency_key": "i-decide",
        },
        headers=ORIGIN,
    ).json()
    return decided["id"]


def _grant_and_start(
    http: TestClient,
    *,
    plan: dict[str, object],
    source_root: Path,
    go_key: str,
    start_key: str,
    correction: bool = False,
    prior_execution_id: str | None = None,
    observations: str = "",
) -> dict[str, object]:
    body: dict[str, object] = {
        "expected_version": plan["plan_version"],
        "idempotency_key": go_key,
        "source_root": str(source_root),
        "correction": correction,
        "review_observations": observations,
    }
    if prior_execution_id:
        body["prior_execution_id"] = prior_execution_id
    preview = http.post(
        f"/api/cursor/plans/{plan['id']}/request-execute-go",
        json=body,
        headers=ORIGIN,
    ).json()
    granted = http.post(
        f"/api/approvals/{preview['approval']['id']}/decide",
        json={"grant": True},
        headers=ORIGIN,
    ).json()
    return http.post(
        f"/api/cursor/plans/{plan['id']}/executions",
        json={
            "approval_id": granted["id"],
            "idempotency_key": start_key,
            "payload_json": preview["payload_json"],
            "payload_hash": preview["payload_hash"],
        },
        headers=ORIGIN,
    ).json()


def test_integrate_local_branch_and_correction_limit(
    client: tuple[TestClient, Path],
) -> None:
    http, git_root = client
    review_id = _decided_review(http)
    plan = http.post(
        f"/api/tech/reviews/{review_id}/cursor-plans",
        json={},
        headers=ORIGIN,
    ).json()
    first = _grant_and_start(
        http, plan=plan, source_root=git_root, go_key="ig-go", start_key="ig-st"
    )
    assert first["capture_manifest_sha"]
    assert not first["capture_incomplete"]
    integ_preview = http.post(
        f"/api/cursor/executions/{first['id']}/request-integrate-go",
        json={"idempotency_key": "ig-igo"},
        headers=ORIGIN,
    ).json()
    http.post(
        f"/api/approvals/{integ_preview['approval']['id']}/decide",
        json={"grant": True},
        headers=ORIGIN,
    )
    applied = http.post(
        f"/api/cursor/executions/{first['id']}/integrate",
        json={
            "approval_id": integ_preview["approval"]["id"],
            "idempotency_key": "ig-apply",
        },
        headers=ORIGIN,
    ).json()
    assert applied["status"] == "applied"
    assert applied["branch_name"].startswith("devcom/cursor/")
    assert applied["commit_sha"]
    assert "cherry-pick" in (applied["merge_hint"] or "")
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=git_root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert status.stdout.strip() == ""
    plan = http.get(f"/api/cursor/plans/{plan['id']}", headers=ORIGIN).json()
    second = _grant_and_start(
        http,
        plan=plan,
        source_root=git_root,
        go_key="corr-go-1",
        start_key="corr-st-1",
        correction=True,
        prior_execution_id=str(first["id"]),
        observations="fix greet edge case from review",
    )
    assert second["correction_index"] == 1
    plan = http.get(f"/api/cursor/plans/{plan['id']}", headers=ORIGIN).json()
    third = _grant_and_start(
        http,
        plan=plan,
        source_root=git_root,
        go_key="corr-go-2",
        start_key="corr-st-2",
        correction=True,
        prior_execution_id=str(second["id"]),
        observations="second correction observations",
    )
    assert third["correction_index"] == 2
    plan = http.get(f"/api/cursor/plans/{plan['id']}", headers=ORIGIN).json()
    blocked = http.post(
        f"/api/cursor/plans/{plan['id']}/request-execute-go",
        json={
            "expected_version": plan["plan_version"],
            "idempotency_key": "corr-go-3",
            "source_root": str(git_root),
            "correction": True,
            "prior_execution_id": third["id"],
            "review_observations": "should fail",
        },
        headers=ORIGIN,
    )
    assert blocked.status_code >= 400
