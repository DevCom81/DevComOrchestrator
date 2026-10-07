from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "devcom" / "demo"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DEVCOM_",
        env_file=".env",
        extra="ignore",
    )

    mode: str = "demo"
    host: str = "127.0.0.1"
    port: int = 8765
    data_dir: Path = Field(default_factory=lambda: DEFAULT_DATA_DIR)
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    allowed_hosts: str = "127.0.0.1:8765,localhost:8765"
    app_name: str = "DevCom Command Center"
    version: str = "0.1.0"
    contracts_dir: Path = Field(default_factory=lambda: REPO_ROOT / "contracts" / "agents")
    frontend_dist: Path = Field(default_factory=lambda: REPO_ROOT / "frontend" / "dist")

    @field_validator("mode")
    @classmethod
    def demo_only(cls, value: str) -> str:
        if value != "demo":
            raise ValueError("lot 0 supports DEVCOM_MODE=demo only")
        return value

    @property
    def database_path(self) -> Path:
        return self.data_dir / "demo.sqlite"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [item.strip().lower() for item in self.allowed_hosts.split(",") if item.strip()]

    @property
    def mutation_origin_list(self) -> list[str]:
        served = [
            f"http://{self.host}:{self.port}",
            f"http://127.0.0.1:{self.port}",
            f"http://localhost:{self.port}",
        ]
        return list(dict.fromkeys([*self.cors_origin_list, *served]))

    def ensure_data_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_data_dir()
    return settings
