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
from devcom.modules.missions.tech.cursor.adapters.fake_cursor_agent import FakeCursorAgent
from devcom.modules.projects.adapters import code_context_models as _code  # noqa: F401
from devcom.modules.projects.adapters import sqlalchemy_models as _projects  # noqa: F401
from devcom.shared.persistence import Base

REPO_ROOT = Path(__file__).resolve().parents[3]
ORIGIN = {"Origin": "http://127.0.0.1:5173"}


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[tuple[TestClient, object, Path]]:
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
        yield test_client, container, git_root


def _decided_review(http: TestClient) -> str:
    project = http.post(
        "/api/projects",
        json={"name": "E", "description": "exec"},
        headers=ORIGIN,
    ).json()["id"]
    review = http.post(
        "/api/tech/reviews",
        json={
            "project_id": project,
            "request_text": "Besoin d'une option",
            "idempotency_key": "e-create",
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
        json={"idempotency_key": "e-run"},
        headers=ORIGIN,
    ).json()
    proposal = next(item for item in ran["proposals"] if not item["blocked"])
    decided = http.post(
        f"/api/tech/reviews/{review['id']}/decision",
        json={
            "proposal_id": proposal["id"],
            "proposal_version": ran["proposals_version"],
            "rationale": "go",
            "idempotency_key": "e-decide",
        },
        headers=ORIGIN,
    ).json()
    return decided["id"]


def test_execute_idempotent_capture_and_no_secret_leak(
    client: tuple[TestClient, object, Path],
) -> None:
    http, container, git_root = client
    review_id = _decided_review(http)
    plan = http.post(
        f"/api/tech/reviews/{review_id}/cursor-plans",
        json={},
        headers=ORIGIN,
    ).json()
    preview = http.post(
        f"/api/cursor/plans/{plan['id']}/request-execute-go",
        json={
            "expected_version": plan["plan_version"],
            "idempotency_key": "ex-go-1",
            "source_root": str(git_root),
        },
        headers=ORIGIN,
    ).json()
    assert "devcom_reservation_eur_micros" in preview["budget_layers"]
    assert "provider_guarantee" in preview["budget_layers"]
    granted = http.post(
        f"/api/approvals/{preview['approval']['id']}/decide",
        json={"grant": True},
        headers=ORIGIN,
    ).json()
    assert granted["status"] == "granted"
    body = {
        "approval_id": granted["id"],
        "idempotency_key": "ex-start-1",
        "payload_json": preview["payload_json"],
        "payload_hash": preview["payload_hash"],
    }
    first = http.post(
        f"/api/cursor/plans/{plan['id']}/executions",
        json=body,
        headers=ORIGIN,
    ).json()
    second = http.post(
        f"/api/cursor/plans/{plan['id']}/executions",
        json=body,
        headers=ORIGIN,
    ).json()
    assert first["id"] == second["id"]
    assert first["status"] in {"return_ready", "finished", "capture_incomplete"}
    assert first["return_id"]
    assert isinstance(container.cursor.cursor_agent, FakeCursorAgent)
    assert len(container.cursor.cursor_agent.calls) == 1
    returns = http.get(f"/api/cursor/plans/{plan['id']}/returns", headers=ORIGIN).json()
    assert returns["items"][0]["execution_id"] == first["id"]
    # no secret in error surfaces
    assert "CURSOR_API_KEY" not in str(first)


def test_real_settings_reject_fake_and_missing_key() -> None:
    with pytest.raises(ValueError, match="forbids"):
        Settings(mode="real", cursor_adapter="fake", llm_adapter="fake")
    with pytest.raises(ValueError, match="CURSOR_API_KEY"):
        Settings(mode="real", cursor_adapter="real", llm_adapter="fake", cursor_api_key=None)


def test_env_loader_does_not_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from devcom.bootstrap.env_loader import load_dotenv_file

    path = tmp_path / ".env"
    path.write_text("FOO=fromfile\nBAR=fileonly\n", encoding="utf-8")
    monkeypatch.setenv("FOO", "fromenv")
    monkeypatch.delenv("BAR", raising=False)
    loaded = load_dotenv_file(path)
    assert "BAR" in loaded
    assert "FOO" not in loaded
    import os

    assert os.environ["FOO"] == "fromenv"
    assert os.environ["BAR"] == "fileonly"
