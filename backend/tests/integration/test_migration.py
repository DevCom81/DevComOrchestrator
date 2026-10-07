from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from devcom.bootstrap.settings import Settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_alembic_upgrade_creates_projects(tmp_path: Path, monkeypatch) -> None:
    data_dir = tmp_path / "migrate-data"
    data_dir.mkdir()
    monkeypatch.setenv("DEVCOM_MODE", "demo")
    monkeypatch.setenv("DEVCOM_DATA_DIR", str(data_dir))

    from devcom.bootstrap.settings import get_settings

    get_settings.cache_clear()
    settings = Settings(
        mode="demo",
        data_dir=data_dir,
        contracts_root=Path(__file__).resolve().parents[3] / "contracts",
    )
    settings.ensure_data_dir()

    # Point alembic env to this data dir via cache clear + env
    monkeypatch.setenv("DEVCOM_DATA_DIR", str(data_dir))
    get_settings.cache_clear()

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("prepend_sys_path", str(BACKEND_ROOT / "src"))
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{settings.database_path}")
    tables = inspect(engine).get_table_names()
    engine.dispose()
    assert "projects" in tables
    get_settings.cache_clear()
