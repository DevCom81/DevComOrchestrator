from pydantic import BaseModel, ConfigDict

from devcom.entrypoints.http.schemas.tech_schemas import BudgetSummaryDto


class RuntimeDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    app_name: str
    version: str
    openai_key_configured: bool
    real_mode_enabled: bool
    budget: BudgetSummaryDto
