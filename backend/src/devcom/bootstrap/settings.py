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
    contracts_root: Path = Field(default_factory=lambda: REPO_ROOT / "contracts")
    frontend_dist: Path = Field(default_factory=lambda: REPO_ROOT / "frontend" / "dist")
    monthly_budget_eur_micros: int = 50_000_000
    review_budget_eur_micros: int = 1_000_000
    llm_adapter: str = "openai"

    @field_validator("mode")
    @classmethod
    def allowed_modes(cls, value: str) -> str:
        if value not in {"demo", "real"}:
            raise ValueError("DEVCOM_MODE must be demo or real")
        return value

    @field_validator("llm_adapter")
    @classmethod
    def allowed_llm(cls, value: str) -> str:
        if value not in {"openai", "fake"}:
            raise ValueError("DEVCOM_LLM_ADAPTER must be openai or fake")
        return value

    @property
    def real_mode_enabled(self) -> bool:
        return self.mode == "real"

    @property
    def agents_contracts_dir(self) -> Path:
        return self.contracts_root / "agents"

    @property
    def capabilities_registry_path(self) -> Path:
        return self.contracts_root / "capabilities" / "registry.json"

    @property
    def permissions_policy_path(self) -> Path:
        return self.contracts_root / "permissions" / "policy.json"

    @property
    def dispatch_rules_path(self) -> Path:
        return self.contracts_root / "dispatch" / "demo_rules.json"

    @property
    def tech_scenarios_index_path(self) -> Path:
        return self.contracts_root / "tech" / "scenarios" / "index.json"

    @property
    def tech_blocking_policy_path(self) -> Path:
        return self.contracts_root / "tech" / "blocking_policy.json"

    @property
    def billing_dir(self) -> Path:
        return self.contracts_root / "billing"

    @property
    def openai_rates_path(self) -> Path:
        return self.billing_dir / "openai_rates_2026-10-07.json"

    @property
    def fx_path(self) -> Path:
        return self.billing_dir / "fx_usd_eur.json"

    @property
    def tech_call_bounds_path(self) -> Path:
        return self.billing_dir / "tech_real_call_bounds.json"

    @property
    def tech_prompts_root(self) -> Path:
        return self.contracts_root / "prompts" / "tech"

    @property
    def filesystem_bounds_path(self) -> Path:
        return self.contracts_root / "filesystem" / "BOUNDS_V1.json"

    @property
    def filesystem_exclusions_path(self) -> Path:
        return self.contracts_root / "filesystem" / "EXCLUSIONS_V1.json"

    @property
    def demo_code_fixture(self) -> Path:
        return self.contracts_root / "demo" / "code_context"

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
